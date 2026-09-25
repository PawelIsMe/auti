from app.config import HA_URL, HA_TOKEN
from typing import Dict, Any, Optional
import requests


headers = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json",
}


def get_ha_entities(domain_filter: Optional[str] = None) -> list[Dict[str, Any]]:
    """
    Pobiera listę wszystkich dostępnych encji z Home Assistanta wraz z ich obecnym stanem i atrybutami.
    Używaj tej funkcji, aby sprawdzić jakie urządzenia są dostępne w domu, poznać ich entity_id oraz aktualny stan.

    Args:
        domain_filter: Opcjonalny filtr domeny encji (np. 'light', 'switch', 'climate', 'sensor', 'cover').
                       Jeśli podany, zwróci tylko encje z tej domeny.

    Returns:
        Lista słowników zawierających: entity_id, state (stan), friendly_name (nazwa czytelna) i atrybuty.
    """
    url = f"{HA_URL}/api/states"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        states = response.json()

        result = []
        for item in states:
            entity_id = item.get("entity_id", "")

            # Filtrowanie po domenie, jeśli podano
            if domain_filter and not entity_id.startswith(f"{domain_filter}."):
                continue

            attributes = item.get("attributes", {})
            result.append({
                "entity_id": entity_id,
                "state": item.get("state"),
                "friendly_name": attributes.get("friendly_name", entity_id),
                "unit_of_measurement": attributes.get("unit_of_measurement"),
                "supported_features": attributes.get("supported_features")
            })

        return result
    except Exception as e:
        return [{"error": f"Błąd podczas pobierania encji HA: {str(e)}"}]


def control_ha_entity(entity_id: str, action: str, service_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Wykonuje akcję (steruje) na konkretnej encji w Home Assistant.

    Args:
        entity_id: Pełny identyfikator encji w HA (np. 'light.swiatlo_salon', 'climate.termostat', 'switch.gniazdko').
        action: Akcja do wykonania (np. 'turn_on', 'turn_off', 'toggle', 'set_temperature', 'open_cover').
        service_data: Dodatkowe parametry dla akcji przekazywane w JSON, np.:
                      - Dla światła: {"brightness": 150, "rgb_color": [255, 0, 0]}
                      - Dla klimatyzacji: {"temperature": 21.5}
                      - Dla rolet: {"position": 50}

    Returns:
        Słownik z bilansem wykonania usługi lub informacją o błędzie.
    """
    domain = entity_id.split(".")[0]
    url = f"{HA_URL}/api/services/{domain}/{action}"

    payload = {"entity_id": entity_id}
    if service_data:
        payload.update(service_data)

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return {
            "status": "success",
            "message": f"Pomyślnie wywołano usługę {domain}.{action} dla {entity_id}",
            "response": response.json()
        }
    except Exception as e:
        return {"status": "error", "message": f"Błąd podczas sterowania {entity_id}: {str(e)}"}


# TODO zdjęcia z kamery (każdy indywidualnie)
# def take_camera_snapshot() -> str:
#     """
#     Robi aktualne zdjęcie (snapshot) z kamery na podwórku.
#     Użyj tej funkcji zawsze, gdy użytkownik prosi o pokazanie obrazu z kamery,
#     pyta co widać na podwórku, lub chce zobaczyć widok z kamery.
#     """
#     url = f"{HA_URL}/api/camera_proxy/{your_camera_entity}"
#     headers = {"Authorization": f"Bearer {HA_TOKEN}"}
#
#     response = requests.get(url, headers=headers)
#
#     if response.status_code == 200:
#         with open("data/static_snapshot.jpg", "wb") as f:
#             f.write(response.content)
#         return "SUCCESS: Obraz z kamery został przechwycony."
#     else:
#         return f"ERROR: Nie udało się pobrać obrazu z HA (Status: {response.status_code})"
