import requests
import re

def get_location_name(coordinates):
    """
    Convert coordinates to a human-readable location name using Nominatim API (OpenStreetMap)
    Format expected: "latitude, longitude"
    """
    if not coordinates or coordinates == "Unknown" or coordinates == "Lokasi tidak terdeteksi":
        return {"name": "Lokasi tidak diketahui", "coordinates": None}
        
    
    coord_pattern = re.compile(r"(-?\d+\.\d+),\s*(-?\d+\.\d+)")
    match = coord_pattern.match(coordinates)
    
    if not match:
        return {"name": coordinates, "coordinates": None}  
        
    lat, lon = match.groups()
    
    try:
        
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        headers = {
            "User-Agent": "AbsensiApp/1.0"  
        }
        
        response = requests.get(url, headers=headers)
        data = response.json()
        
        
        if "display_name" in data:
            
            address_parts = []
            
            
            for key in ["road", "suburb", "city", "town", "village", "district", "county", "state"]:
                if key in data.get("address", {}) and data["address"][key]:
                    address_parts.append(data["address"][key])
                    if len(address_parts) >= 2:  
                        break
            
            if not address_parts and "display_name" in data:
                # Jika tidak ada bagian alamat spesifik, gunakan dua bagian pertama dari display_name
                location_name = data["display_name"].split(',')[0:2]
                location_name = ', '.join(location_name)
            else:
                # Gabungkan bagian alamat yang ditemukan
                location_name = ', '.join(address_parts)
                
            return {
                "name": location_name,
                "coordinates": f"{lat},{lon}"
            }
        
        # Jika tidak ada display_name, kembalikan format default
        return {"name": f"Lokasi ({lat}, {lon})", "coordinates": f"{lat},{lon}"}
        
    except Exception as e:
        # Tangani error saat request ke API lokasi
        print(f"Error getting location name: {str(e)}")
        return {"name": f"Lokasi ({lat}, {lon})", "coordinates": f"{lat},{lon}"}

def get_google_maps_url(coordinates):
    """Generate Google Maps URL from coordinates"""
    if not coordinates:
        # Jika koordinat tidak valid, kembalikan link kosong
        return "#"
    
    # Hilangkan spasi dan buat URL Google Maps
    coordinates = coordinates.replace(" ", "")
    return f"https://www.google.com/maps?q={coordinates}"
