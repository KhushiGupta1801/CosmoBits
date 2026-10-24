"""Tests for the debris data formatter."""

import json

import data_formatter


def _sample_records():
    return [
        {"OBJECT_NAME": "GOOD OBJ 1"},
        {"OBJECT_NAME": "GOOD OBJ 2"},
        {"OBJECT_NAME": "BAD RANGE"},
        {"OBJECT_NAME": "BAD PROP"},
    ]


def test_get_formatted_data_returns_list(monkeypatch):
    """The formatter should return a list of valid records."""

    def fake_fetch_debris():
        return _sample_records()

    def fake_propagate(record, now):
        name = record["OBJECT_NAME"]
        if name == "BAD RANGE":
            return (91.0, 0.0, 100.0)
        if name == "BAD PROP":
            raise ValueError("bad propagation")
        return ({"GOOD OBJ 1": (10.1234, 20.2345, 100.0), "GOOD OBJ 2": (-10.0, 179.9999, 55.0)})[name]

    monkeypatch.setattr(data_formatter, "fetch_debris", fake_fetch_debris)
    monkeypatch.setattr(data_formatter, "propagate_record", fake_propagate)

    result = data_formatter.get_formatted_data()

    assert isinstance(result, list)
    assert len(result) == 2
    for item in result:
        assert set(item.keys()) == {"name", "latitude", "longitude", "altitude"}
        assert -90 <= item["latitude"] <= 90
        assert -180 <= item["longitude"] <= 180
        assert item["altitude"] > 0


def test_get_json_returns_valid_json(monkeypatch):
    """The JSON helper should serialize and parse back to the same values."""

    def fake_fetch_debris():
        return _sample_records()

    def fake_propagate(record, now):
        name = record["OBJECT_NAME"]
        if name == "BAD RANGE":
            return (91.0, 0.0, 100.0)
        if name == "BAD PROP":
            raise ValueError("bad propagation")
        return ({"GOOD OBJ 1": (10.1234, 20.2345, 100.0), "GOOD OBJ 2": (-10.0, 179.9999, 55.0)})[name]

    monkeypatch.setattr(data_formatter, "fetch_debris", fake_fetch_debris)
    monkeypatch.setattr(data_formatter, "propagate_record", fake_propagate)

    raw = data_formatter.get_json()
    decoded = json.loads(raw)
    assert decoded == data_formatter.get_formatted_data()
