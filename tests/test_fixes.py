"""Тесты без сети: qBittorrent и внешние API замоканы."""
from unittest.mock import MagicMock, patch

import pytest

import src.qbittorrent_client as qb
import src.tmdb_api as tmdb
import src.kinopoisk_api as kp
from src.message_tools import Message_data
from src.metadata_tools import Metadata, MetadataError, get_name_torrent

HEX_HASH = "1f6b39581bd5c4b89cc8bdc1543ee255382431b2"


# --- info hash ---------------------------------------------------------------
def test_get_info_hash_hex():
    assert qb.get_info_hash(f"magnet:?xt=urn:btih:{HEX_HASH.upper()}&dn=x") == HEX_HASH


def test_get_info_hash_base32():
    import base64
    b32 = base64.b32encode(bytes.fromhex(HEX_HASH)).decode()
    assert qb.get_info_hash(f"magnet:?xt=urn:btih:{b32}") == HEX_HASH


def test_get_info_hash_invalid():
    with pytest.raises(qb.GetInfoFromMagnet):
        qb.get_info_hash("magnet:?xt=urn:AAAA")


# --- получение метаданных через qBittorrent ----------------------------------
def make_client(existing):
    client = MagicMock()
    client.torrents_info.return_value = [{"name": "Film"}] if existing else []
    client.torrents_files.return_value = [{"name": "Film/film.mkv", "size": 1}]
    client.torrents_trackers.return_value = []
    if not existing:
        # после добавления торрент появляется в клиенте
        client.torrents_info.side_effect = [[], [{"name": "Film"}]]
    return client


def test_qb_metadata_does_not_delete_existing_torrent():
    client = make_client(existing=True)
    with patch.object(qb, "client", client):
        data = qb.get_info_from_magnet_by_qb(f"magnet:?xt=urn:btih:{HEX_HASH}")
    assert data["data"]["name"] == "Film"
    client.torrents_add.assert_not_called()
    client.torrents_delete.assert_not_called()


def test_qb_metadata_deletes_own_temp_torrent():
    client = make_client(existing=False)
    with patch.object(qb, "client", client):
        qb.get_info_from_magnet_by_qb(f"magnet:?xt=urn:btih:{HEX_HASH}")
    client.torrents_add.assert_called_once()
    client.torrents_delete.assert_called_once_with(delete_files=True, torrent_hashes=HEX_HASH)


def test_qb_metadata_timeout_raises_clear_error():
    client = make_client(existing=False)
    client.torrents_files.return_value = []
    with patch.object(qb, "client", client), patch.object(qb, "METADATA_RETRY_DELAY", 0):
        with pytest.raises(qb.GetInfoFromMagnet):
            qb.get_info_from_magnet_by_qb(f"magnet:?xt=urn:btih:{HEX_HASH}")
    client.torrents_delete.assert_called_once()


def test_add_torrent_reports_fails():
    client = MagicMock()
    client.torrents_add.return_value = "Fails."
    with patch.object(qb, "client", client):
        assert "не добавил" in qb.add_torrent_from_magnet("magnet:?xt=urn:btih:x")


# --- Metadata ----------------------------------------------------------------
def fake_meta(name, files):
    return {"data": {"name": name, "files": files}}


def test_metadata_returns_independent_instances():
    with patch("src.metadata_tools.get_metadata_api",
               side_effect=[fake_meta("A", [{"name": "a.mkv", "path": "a.mkv"}]),
                            fake_meta("B", [{"name": "b.txt", "path": "B/b.txt"}])]):
        a = Metadata.prepare_from_magnet("m1")
        b = Metadata.prepare_from_magnet("m2")
    assert isinstance(a, Metadata)
    assert (a.name, a.inDir, a.isMovies) == ("A", False, True)
    assert (b.name, b.inDir, b.isMovies) == ("B", True, False)


def test_metadata_none_raises():
    with patch("src.metadata_tools.get_metadata_api", return_value=None):
        with pytest.raises(MetadataError):
            Metadata.prepare_from_magnet("m")


def test_get_name_torrent_without_name():
    assert get_name_torrent(Message_data(), Metadata(name=None)) == "Без названия"


# --- TMDB --------------------------------------------------------------------
def tmdb_response(results):
    resp = MagicMock()
    resp.json.return_value = {"total_results": len(results), "results": results}
    return resp


def test_tmdb_series_original_name(message_serials_gto):
    results = [
        {"id": 1, "name": "Other", "original_name": "Other"},
        {"id": 2, "name": "GTO", "original_name": "GTO: Great Teacher Onizuka"},
    ]
    with patch("src.tmdb_api.requests.get", return_value=tmdb_response(results)) as get:
        assert tmdb.get_id_tmdb(message_serials_gto) == 2
    assert get.call_args.kwargs["params"]["query"] == "GTO: Great Teacher Onizuka"


def test_tmdb_query_passed_as_params():
    md = Message_data(title="Тест", alternative_title="Tom & Jerry", year=1990)
    with patch("src.tmdb_api.requests.get", return_value=tmdb_response([{"id": 5}])) as get:
        assert tmdb.get_id_tmdb(md) == 5
    assert "?" not in get.call_args.args[0]
    assert get.call_args.kwargs["params"]["query"] == "Tom & Jerry"


# --- Кинопоиск ---------------------------------------------------------------
def test_kinopoisk_no_year_returns_zero():
    with patch("src.kinopoisk_api.requests.get") as get:
        assert kp.get_id_kinopoisk(Message_data(title="Фильм")) == 0
    get.assert_not_called()


def test_qb_metadata_waits_when_torrent_not_registered_yet():
    # сразу после torrents_add qBittorrent может ответить 404 на запрос файлов
    import qbittorrentapi
    client = make_client(existing=False)
    client.torrents_files.side_effect = [
        qbittorrentapi.NotFound404Error("Torrent hash not found"),
        qbittorrentapi.NotFound404Error("Torrent hash not found"),
        [],
        [{"name": "Film/film.mkv", "size": 1}],
    ]
    with patch.object(qb, "client", client), patch.object(qb, "METADATA_RETRY_DELAY", 0):
        data = qb.get_info_from_magnet_by_qb(f"magnet:?xt=urn:btih:{HEX_HASH}")
    assert data["data"]["files"][0]["path"] == "Film/film.mkv"
    assert client.torrents_files.call_count == 4
