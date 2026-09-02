"""Helpers for the pending writes that are sent on the next refresh."""
from __future__ import annotations

from homeassistant.core import HomeAssistant


def queue_update(
    hass: HomeAssistant,
    key: str,
    changes: dict,
    defaults: dict | None = None,
) -> None:
    """Queue a write, keeping the fields other entities already queued.

    The fan takes one struct per mode, so an entity has to send the fields it
    does not own as well. `defaults` holds those companion fields, taken from
    the last reported state, and is only used for fields that are not already
    waiting to be written. `changes` holds the fields the entity is actually
    setting and always wins, so two entities writing to the same mode before
    the debounced refresh runs no longer overwrite each other.
    """
    merged = dict(defaults or {})
    merged.update(hass.data.get(key) or {})
    merged.update(changes)

    hass.data[key] = merged
