"""World cities database for satellite access window calculations.

This module contains a comprehensive database of world cities including capitals
and major metropolitan areas with their geographic coordinates and elevations.
"""

from typing import Dict, List, Optional
import json

# Comprehensive world cities database
WORLD_CITIES = {
    # North America - USA
    "new york": {"name": "New York", "country": "USA", "latitude": 40.7128, "longitude": -74.0060, "altitude": 10, "type": "major_city"},
    "los angeles": {"name": "Los Angeles", "country": "USA", "latitude": 34.0522, "longitude": -118.2437, "altitude": 71, "type": "major_city"},
    "chicago": {"name": "Chicago", "country": "USA", "latitude": 41.8781, "longitude": -87.6298, "altitude": 181, "type": "major_city"},
    "houston": {"name": "Houston", "country": "USA", "latitude": 29.7604, "longitude": -95.3698, "altitude": 13, "type": "major_city"},
    "washington": {"name": "Washington D.C.", "country": "USA", "latitude": 38.9072, "longitude": -77.0369, "altitude": 8, "type": "capital"},
    "washington dc": {"name": "Washington D.C.", "country": "USA", "latitude": 38.9072, "longitude": -77.0369, "altitude": 8, "type": "capital"},
    "boston": {"name": "Boston", "country": "USA", "latitude": 42.3601, "longitude": -71.0589, "altitude": 43, "type": "major_city"},
    "san francisco": {"name": "San Francisco", "country": "USA", "latitude": 37.7749, "longitude": -122.4194, "altitude": 16, "type": "major_city"},
    "seattle": {"name": "Seattle", "country": "USA", "latitude": 47.6062, "longitude": -122.3321, "altitude": 56, "type": "major_city"},
    "miami": {"name": "Miami", "country": "USA", "latitude": 25.7617, "longitude": -80.1918, "altitude": 2, "type": "major_city"},
    "denver": {"name": "Denver", "country": "USA", "latitude": 39.7392, "longitude": -104.9903, "altitude": 1609, "type": "major_city"},
    "atlanta": {"name": "Atlanta", "country": "USA", "latitude": 33.7490, "longitude": -84.3880, "altitude": 320, "type": "major_city"},
    
    # North America - Canada
    "ottawa": {"name": "Ottawa", "country": "Canada", "latitude": 45.4215, "longitude": -75.6972, "altitude": 70, "type": "capital"},
    "toronto": {"name": "Toronto", "country": "Canada", "latitude": 43.6532, "longitude": -79.3832, "altitude": 76, "type": "major_city"},
    "vancouver": {"name": "Vancouver", "country": "Canada", "latitude": 49.2827, "longitude": -123.1207, "altitude": 70, "type": "major_city"},
    "montreal": {"name": "Montreal", "country": "Canada", "latitude": 45.5017, "longitude": -73.5673, "altitude": 233, "type": "major_city"},
    "calgary": {"name": "Calgary", "country": "Canada", "latitude": 51.0447, "longitude": -114.0719, "altitude": 1048, "type": "major_city"},
    
    # North America - Mexico
    "mexico city": {"name": "Mexico City", "country": "Mexico", "latitude": 19.4326, "longitude": -99.1332, "altitude": 2240, "type": "capital"},
    
    # South America
    "buenos aires": {"name": "Buenos Aires", "country": "Argentina", "latitude": -34.6037, "longitude": -58.3816, "altitude": 25, "type": "capital"},
    "brasilia": {"name": "Brasília", "country": "Brazil", "latitude": -15.8267, "longitude": -47.9218, "altitude": 1172, "type": "capital"},
    "brasília": {"name": "Brasília", "country": "Brazil", "latitude": -15.8267, "longitude": -47.9218, "altitude": 1172, "type": "capital"},
    "sao paulo": {"name": "São Paulo", "country": "Brazil", "latitude": -23.5505, "longitude": -46.6333, "altitude": 760, "type": "major_city"},
    "são paulo": {"name": "São Paulo", "country": "Brazil", "latitude": -23.5505, "longitude": -46.6333, "altitude": 760, "type": "major_city"},
    "rio de janeiro": {"name": "Rio de Janeiro", "country": "Brazil", "latitude": -22.9068, "longitude": -43.1729, "altitude": 2, "type": "major_city"},
    "lima": {"name": "Lima", "country": "Peru", "latitude": -12.0464, "longitude": -77.0428, "altitude": 154, "type": "capital"},
    "bogota": {"name": "Bogotá", "country": "Colombia", "latitude": 4.7110, "longitude": -74.0721, "altitude": 2625, "type": "capital"},
    "bogotá": {"name": "Bogotá", "country": "Colombia", "latitude": 4.7110, "longitude": -74.0721, "altitude": 2625, "type": "capital"},
    "caracas": {"name": "Caracas", "country": "Venezuela", "latitude": 10.4806, "longitude": -66.9036, "altitude": 900, "type": "capital"},
    "santiago": {"name": "Santiago", "country": "Chile", "latitude": -33.4489, "longitude": -70.6693, "altitude": 520, "type": "capital"},
    "quito": {"name": "Quito", "country": "Ecuador", "latitude": -0.1807, "longitude": -78.4678, "altitude": 2850, "type": "capital"},
    "la paz": {"name": "La Paz", "country": "Bolivia", "latitude": -16.5000, "longitude": -68.1193, "altitude": 3500, "type": "capital"},
    
    # Europe - Western
    "london": {"name": "London", "country": "UK", "latitude": 51.5074, "longitude": -0.1278, "altitude": 11, "type": "capital"},
    "paris": {"name": "Paris", "country": "France", "latitude": 48.8566, "longitude": 2.3522, "altitude": 35, "type": "capital"},
    "berlin": {"name": "Berlin", "country": "Germany", "latitude": 52.5200, "longitude": 13.4050, "altitude": 34, "type": "capital"},
    "madrid": {"name": "Madrid", "country": "Spain", "latitude": 40.4168, "longitude": -3.7038, "altitude": 650, "type": "capital"},
    "rome": {"name": "Rome", "country": "Italy", "latitude": 41.9028, "longitude": 12.4964, "altitude": 21, "type": "capital"},
    "amsterdam": {"name": "Amsterdam", "country": "Netherlands", "latitude": 52.3676, "longitude": 4.9041, "altitude": -2, "type": "capital"},
    "brussels": {"name": "Brussels", "country": "Belgium", "latitude": 50.8503, "longitude": 4.3517, "altitude": 56, "type": "capital"},
    "vienna": {"name": "Vienna", "country": "Austria", "latitude": 48.2082, "longitude": 16.3738, "altitude": 171, "type": "capital"},
    "zurich": {"name": "Zurich", "country": "Switzerland", "latitude": 47.3769, "longitude": 8.5417, "altitude": 408, "type": "major_city"},
    "bern": {"name": "Bern", "country": "Switzerland", "latitude": 46.9480, "longitude": 7.4474, "altitude": 540, "type": "capital"},
    "lisbon": {"name": "Lisbon", "country": "Portugal", "latitude": 38.7223, "longitude": -9.1393, "altitude": 2, "type": "capital"},
    "dublin": {"name": "Dublin", "country": "Ireland", "latitude": 53.3498, "longitude": -6.2603, "altitude": 20, "type": "capital"},
    "copenhagen": {"name": "Copenhagen", "country": "Denmark", "latitude": 55.6761, "longitude": 12.5683, "altitude": 24, "type": "capital"},
    "stockholm": {"name": "Stockholm", "country": "Sweden", "latitude": 59.3293, "longitude": 18.0686, "altitude": 28, "type": "capital"},
    "oslo": {"name": "Oslo", "country": "Norway", "latitude": 59.9139, "longitude": 10.7522, "altitude": 23, "type": "capital"},
    "helsinki": {"name": "Helsinki", "country": "Finland", "latitude": 60.1699, "longitude": 24.9384, "altitude": 26, "type": "capital"},
    
    # Europe - Eastern
    "moscow": {"name": "Moscow", "country": "Russia", "latitude": 55.7558, "longitude": 37.6176, "altitude": 156, "type": "capital"},
    "st petersburg": {"name": "St. Petersburg", "country": "Russia", "latitude": 59.9311, "longitude": 30.3609, "altitude": 3, "type": "major_city"},
    "warsaw": {"name": "Warsaw", "country": "Poland", "latitude": 52.2297, "longitude": 21.0122, "altitude": 113, "type": "capital"},
    "prague": {"name": "Prague", "country": "Czech Republic", "latitude": 50.0755, "longitude": 14.4378, "altitude": 200, "type": "capital"},
    "budapest": {"name": "Budapest", "country": "Hungary", "latitude": 47.4979, "longitude": 19.0402, "altitude": 102, "type": "capital"},
    "bucharest": {"name": "Bucharest", "country": "Romania", "latitude": 44.4268, "longitude": 26.1025, "altitude": 90, "type": "capital"},
    "kiev": {"name": "Kiev", "country": "Ukraine", "latitude": 50.4501, "longitude": 30.5234, "altitude": 179, "type": "capital"},
    "kyiv": {"name": "Kyiv", "country": "Ukraine", "latitude": 50.4501, "longitude": 30.5234, "altitude": 179, "type": "capital"},
    "zagreb": {"name": "Zagreb", "country": "Croatia", "latitude": 45.8150, "longitude": 15.9819, "altitude": 158, "type": "capital"},
    "belgrade": {"name": "Belgrade", "country": "Serbia", "latitude": 44.7866, "longitude": 20.4489, "altitude": 117, "type": "capital"},
    "sofia": {"name": "Sofia", "country": "Bulgaria", "latitude": 42.6977, "longitude": 23.3219, "altitude": 550, "type": "capital"},
    "athens": {"name": "Athens", "country": "Greece", "latitude": 37.9838, "longitude": 23.7275, "altitude": 170, "type": "capital"},
    
    # Asia - East
    "beijing": {"name": "Beijing", "country": "China", "latitude": 39.9042, "longitude": 116.4074, "altitude": 43, "type": "capital"},
    "shanghai": {"name": "Shanghai", "country": "China", "latitude": 31.2304, "longitude": 121.4737, "altitude": 4, "type": "major_city"},
    "hong kong": {"name": "Hong Kong", "country": "Hong Kong", "latitude": 22.3193, "longitude": 114.1694, "altitude": 8, "type": "major_city"},
    "tokyo": {"name": "Tokyo", "country": "Japan", "latitude": 35.6762, "longitude": 139.6503, "altitude": 6, "type": "capital"},
    "osaka": {"name": "Osaka", "country": "Japan", "latitude": 34.6937, "longitude": 135.5023, "altitude": 5, "type": "major_city"},
    "seoul": {"name": "Seoul", "country": "South Korea", "latitude": 37.5665, "longitude": 126.9780, "altitude": 38, "type": "capital"},
    "taipei": {"name": "Taipei", "country": "Taiwan", "latitude": 25.0330, "longitude": 121.5654, "altitude": 9, "type": "capital"},
    "pyongyang": {"name": "Pyongyang", "country": "North Korea", "latitude": 39.0392, "longitude": 125.7625, "altitude": 38, "type": "capital"},
    "ulaanbaatar": {"name": "Ulaanbaatar", "country": "Mongolia", "latitude": 47.8864, "longitude": 106.9057, "altitude": 1350, "type": "capital"},
    
    # Asia - Southeast
    "singapore": {"name": "Singapore", "country": "Singapore", "latitude": 1.3521, "longitude": 103.8198, "altitude": 15, "type": "capital"},
    "bangkok": {"name": "Bangkok", "country": "Thailand", "latitude": 13.7563, "longitude": 100.5018, "altitude": 1, "type": "capital"},
    "kuala lumpur": {"name": "Kuala Lumpur", "country": "Malaysia", "latitude": 3.1390, "longitude": 101.6869, "altitude": 22, "type": "capital"},
    "jakarta": {"name": "Jakarta", "country": "Indonesia", "latitude": -6.2088, "longitude": 106.8456, "altitude": 8, "type": "capital"},
    "manila": {"name": "Manila", "country": "Philippines", "latitude": 14.5995, "longitude": 120.9842, "altitude": 16, "type": "capital"},
    "hanoi": {"name": "Hanoi", "country": "Vietnam", "latitude": 21.0285, "longitude": 105.8542, "altitude": 6, "type": "capital"},
    "ho chi minh city": {"name": "Ho Chi Minh City", "country": "Vietnam", "latitude": 10.8231, "longitude": 106.6297, "altitude": 5, "type": "major_city"},
    "phnom penh": {"name": "Phnom Penh", "country": "Cambodia", "latitude": 11.5564, "longitude": 104.9282, "altitude": 12, "type": "capital"},
    "vientiane": {"name": "Vientiane", "country": "Laos", "latitude": 17.9757, "longitude": 102.6331, "altitude": 174, "type": "capital"},
    "yangon": {"name": "Yangon", "country": "Myanmar", "latitude": 16.8661, "longitude": 96.1951, "altitude": 25, "type": "major_city"},
    "naypyidaw": {"name": "Naypyidaw", "country": "Myanmar", "latitude": 19.7633, "longitude": 96.0785, "altitude": 115, "type": "capital"},
    "bandar seri begawan": {"name": "Bandar Seri Begawan", "country": "Brunei", "latitude": 4.9031, "longitude": 114.9398, "altitude": 1, "type": "capital"},
    
    # Asia - South
    "new delhi": {"name": "New Delhi", "country": "India", "latitude": 28.6139, "longitude": 77.2090, "altitude": 216, "type": "capital"},
    "delhi": {"name": "Delhi", "country": "India", "latitude": 28.7041, "longitude": 77.1025, "altitude": 200, "type": "major_city"},
    "mumbai": {"name": "Mumbai", "country": "India", "latitude": 19.0760, "longitude": 72.8777, "altitude": 14, "type": "major_city"},
    "bangalore": {"name": "Bangalore", "country": "India", "latitude": 12.9716, "longitude": 77.5946, "altitude": 920, "type": "major_city"},
    "chennai": {"name": "Chennai", "country": "India", "latitude": 13.0827, "longitude": 80.2707, "altitude": 6, "type": "major_city"},
    "kolkata": {"name": "Kolkata", "country": "India", "latitude": 22.5726, "longitude": 88.3639, "altitude": 9, "type": "major_city"},
    "hyderabad": {"name": "Hyderabad", "country": "India", "latitude": 17.3850, "longitude": 78.4867, "altitude": 542, "type": "major_city"},
    "islamabad": {"name": "Islamabad", "country": "Pakistan", "latitude": 33.6844, "longitude": 73.0479, "altitude": 507, "type": "capital"},
    "karachi": {"name": "Karachi", "country": "Pakistan", "latitude": 24.8607, "longitude": 67.0011, "altitude": 8, "type": "major_city"},
    "lahore": {"name": "Lahore", "country": "Pakistan", "latitude": 31.5204, "longitude": 74.3587, "altitude": 217, "type": "major_city"},
    "dhaka": {"name": "Dhaka", "country": "Bangladesh", "latitude": 23.8103, "longitude": 90.4125, "altitude": 8, "type": "capital"},
    "colombo": {"name": "Colombo", "country": "Sri Lanka", "latitude": 6.9271, "longitude": 79.8612, "altitude": 1, "type": "capital"},
    "kathmandu": {"name": "Kathmandu", "country": "Nepal", "latitude": 27.7172, "longitude": 85.3240, "altitude": 1400, "type": "capital"},
    "thimphu": {"name": "Thimphu", "country": "Bhutan", "latitude": 27.4728, "longitude": 89.6390, "altitude": 2320, "type": "capital"},
    "male": {"name": "Malé", "country": "Maldives", "latitude": 4.1755, "longitude": 73.5093, "altitude": 1, "type": "capital"},
    "kabul": {"name": "Kabul", "country": "Afghanistan", "latitude": 34.5553, "longitude": 69.2075, "altitude": 1790, "type": "capital"},
    
    # Asia - Central & Western
    "tashkent": {"name": "Tashkent", "country": "Uzbekistan", "latitude": 41.2995, "longitude": 69.2401, "altitude": 455, "type": "capital"},
    "almaty": {"name": "Almaty", "country": "Kazakhstan", "latitude": 43.2220, "longitude": 76.8512, "altitude": 682, "type": "major_city"},
    "nur-sultan": {"name": "Nur-Sultan", "country": "Kazakhstan", "latitude": 51.1605, "longitude": 71.4704, "altitude": 347, "type": "capital"},
    "astana": {"name": "Astana", "country": "Kazakhstan", "latitude": 51.1605, "longitude": 71.4704, "altitude": 347, "type": "capital"},
    "bishkek": {"name": "Bishkek", "country": "Kyrgyzstan", "latitude": 42.8746, "longitude": 74.5698, "altitude": 800, "type": "capital"},
    "dushanbe": {"name": "Dushanbe", "country": "Tajikistan", "latitude": 38.5598, "longitude": 68.7870, "altitude": 750, "type": "capital"},
    "ashgabat": {"name": "Ashgabat", "country": "Turkmenistan", "latitude": 37.9601, "longitude": 58.3261, "altitude": 219, "type": "capital"},
    "tehran": {"name": "Tehran", "country": "Iran", "latitude": 35.6892, "longitude": 51.3890, "altitude": 1190, "type": "capital"},
    "baghdad": {"name": "Baghdad", "country": "Iraq", "latitude": 33.3152, "longitude": 44.3661, "altitude": 34, "type": "capital"},
    "damascus": {"name": "Damascus", "country": "Syria", "latitude": 33.5138, "longitude": 36.2765, "altitude": 680, "type": "capital"},
    "beirut": {"name": "Beirut", "country": "Lebanon", "latitude": 33.8938, "longitude": 35.5018, "altitude": 56, "type": "capital"},
    "amman": {"name": "Amman", "country": "Jordan", "latitude": 31.9454, "longitude": 35.9284, "altitude": 757, "type": "capital"},
    "jerusalem": {"name": "Jerusalem", "country": "Israel", "latitude": 31.7683, "longitude": 35.2137, "altitude": 754, "type": "capital"},
    "tel aviv": {"name": "Tel Aviv", "country": "Israel", "latitude": 32.0853, "longitude": 34.7818, "altitude": 5, "type": "major_city"},
    "ankara": {"name": "Ankara", "country": "Turkey", "latitude": 39.9334, "longitude": 32.8597, "altitude": 938, "type": "capital"},
    "istanbul": {"name": "Istanbul", "country": "Turkey", "latitude": 41.0082, "longitude": 28.9784, "altitude": 39, "type": "major_city"},
    "riyadh": {"name": "Riyadh", "country": "Saudi Arabia", "latitude": 24.7136, "longitude": 46.6753, "altitude": 612, "type": "capital"},
    "dubai": {"name": "Dubai", "country": "UAE", "latitude": 25.2048, "longitude": 55.2708, "altitude": 5, "type": "major_city"},
    "abu dhabi": {"name": "Abu Dhabi", "country": "UAE", "latitude": 24.2532, "longitude": 54.3665, "altitude": 5, "type": "capital"},
    "doha": {"name": "Doha", "country": "Qatar", "latitude": 25.2854, "longitude": 51.5310, "altitude": 10, "type": "capital"},
    "kuwait city": {"name": "Kuwait City", "country": "Kuwait", "latitude": 29.3759, "longitude": 47.9774, "altitude": 55, "type": "capital"},
    "manama": {"name": "Manama", "country": "Bahrain", "latitude": 26.0667, "longitude": 50.5577, "altitude": 2, "type": "capital"},
    "muscat": {"name": "Muscat", "country": "Oman", "latitude": 23.5859, "longitude": 58.4059, "altitude": 48, "type": "capital"},
    "sanaa": {"name": "Sana'a", "country": "Yemen", "latitude": 15.3694, "longitude": 44.1910, "altitude": 2250, "type": "capital"},
    "yerevan": {"name": "Yerevan", "country": "Armenia", "latitude": 40.1792, "longitude": 44.4991, "altitude": 1022, "type": "capital"},
    "baku": {"name": "Baku", "country": "Azerbaijan", "latitude": 40.4093, "longitude": 49.8671, "altitude": -25, "type": "capital"},
    "tbilisi": {"name": "Tbilisi", "country": "Georgia", "latitude": 41.7151, "longitude": 44.8271, "altitude": 490, "type": "capital"},
    
    # Africa - Northern
    "cairo": {"name": "Cairo", "country": "Egypt", "latitude": 30.0444, "longitude": 31.2357, "altitude": 74, "type": "capital"},
    "alexandria": {"name": "Alexandria", "country": "Egypt", "latitude": 31.2001, "longitude": 29.9187, "altitude": 12, "type": "major_city"},
    "algiers": {"name": "Algiers", "country": "Algeria", "latitude": 36.7538, "longitude": 3.0588, "altitude": 424, "type": "capital"},
    "tunis": {"name": "Tunis", "country": "Tunisia", "latitude": 36.8065, "longitude": 10.1815, "altitude": 4, "type": "capital"},
    "tripoli": {"name": "Tripoli", "country": "Libya", "latitude": 32.8872, "longitude": 13.1913, "altitude": 81, "type": "capital"},
    "rabat": {"name": "Rabat", "country": "Morocco", "latitude": 34.0209, "longitude": -6.8416, "altitude": 135, "type": "capital"},
    "casablanca": {"name": "Casablanca", "country": "Morocco", "latitude": 33.5731, "longitude": -7.5898, "altitude": 50, "type": "major_city"},
    "khartoum": {"name": "Khartoum", "country": "Sudan", "latitude": 15.5007, "longitude": 32.5599, "altitude": 382, "type": "capital"},
    
    # Africa - Sub-Saharan
    "lagos": {"name": "Lagos", "country": "Nigeria", "latitude": 6.5244, "longitude": 3.3792, "altitude": 39, "type": "major_city"},
    "abuja": {"name": "Abuja", "country": "Nigeria", "latitude": 9.0579, "longitude": 7.4951, "altitude": 840, "type": "capital"},
    "cape town": {"name": "Cape Town", "country": "South Africa", "latitude": -33.9249, "longitude": 18.4241, "altitude": 25, "type": "major_city"},
    "johannesburg": {"name": "Johannesburg", "country": "South Africa", "latitude": -26.2041, "longitude": 28.0473, "altitude": 1753, "type": "major_city"},
    "pretoria": {"name": "Pretoria", "country": "South Africa", "latitude": -25.7479, "longitude": 28.2293, "altitude": 1339, "type": "capital"},
    "nairobi": {"name": "Nairobi", "country": "Kenya", "latitude": -1.2921, "longitude": 36.8219, "altitude": 1795, "type": "capital"},
    "addis ababa": {"name": "Addis Ababa", "country": "Ethiopia", "latitude": 9.1450, "longitude": 40.4897, "altitude": 2355, "type": "capital"},
    "dar es salaam": {"name": "Dar es Salaam", "country": "Tanzania", "latitude": -6.7924, "longitude": 39.2083, "altitude": 48, "type": "major_city"},
    "dodoma": {"name": "Dodoma", "country": "Tanzania", "latitude": -6.1630, "longitude": 35.7516, "altitude": 1120, "type": "capital"},
    "kampala": {"name": "Kampala", "country": "Uganda", "latitude": 0.3476, "longitude": 32.5825, "altitude": 1190, "type": "capital"},
    "kigali": {"name": "Kigali", "country": "Rwanda", "latitude": -1.9706, "longitude": 30.1044, "altitude": 1567, "type": "capital"},
    "bujumbura": {"name": "Bujumbura", "country": "Burundi", "latitude": -3.3614, "longitude": 29.3599, "altitude": 782, "type": "capital"},
    "kinshasa": {"name": "Kinshasa", "country": "DR Congo", "latitude": -4.4419, "longitude": 15.2663, "altitude": 240, "type": "capital"},
    "brazzaville": {"name": "Brazzaville", "country": "Congo", "latitude": -4.2634, "longitude": 15.2429, "altitude": 314, "type": "capital"},
    "libreville": {"name": "Libreville", "country": "Gabon", "latitude": 0.4162, "longitude": 9.4673, "altitude": 9, "type": "capital"},
    "yaounde": {"name": "Yaoundé", "country": "Cameroon", "latitude": 3.8480, "longitude": 11.5021, "altitude": 726, "type": "capital"},
    "accra": {"name": "Accra", "country": "Ghana", "latitude": 5.6037, "longitude": -0.1870, "altitude": 61, "type": "capital"},
    "abidjan": {"name": "Abidjan", "country": "Ivory Coast", "latitude": 5.3600, "longitude": -4.0083, "altitude": 76, "type": "major_city"},
    "yamoussoukro": {"name": "Yamoussoukro", "country": "Ivory Coast", "latitude": 6.8276, "longitude": -5.2893, "altitude": 213, "type": "capital"},
    "dakar": {"name": "Dakar", "country": "Senegal", "latitude": 14.7167, "longitude": -17.4677, "altitude": 22, "type": "capital"},
    "bamako": {"name": "Bamako", "country": "Mali", "latitude": 12.6392, "longitude": -8.0029, "altitude": 381, "type": "capital"},
    "ouagadougou": {"name": "Ouagadougou", "country": "Burkina Faso", "latitude": 12.3714, "longitude": -1.5197, "altitude": 306, "type": "capital"},
    "niamey": {"name": "Niamey", "country": "Niger", "latitude": 13.5116, "longitude": 2.1254, "altitude": 207, "type": "capital"},
    "ndjamena": {"name": "N'Djamena", "country": "Chad", "latitude": 12.1348, "longitude": 15.0557, "altitude": 298, "type": "capital"},
    "luanda": {"name": "Luanda", "country": "Angola", "latitude": -8.8383, "longitude": 13.2344, "altitude": 6, "type": "capital"},
    "windhoek": {"name": "Windhoek", "country": "Namibia", "latitude": -22.5609, "longitude": 17.0658, "altitude": 1728, "type": "capital"},
    "gaborone": {"name": "Gaborone", "country": "Botswana", "latitude": -24.6282, "longitude": 25.9231, "altitude": 1014, "type": "capital"},
    "harare": {"name": "Harare", "country": "Zimbabwe", "latitude": -17.8252, "longitude": 31.0335, "altitude": 1483, "type": "capital"},
    "lusaka": {"name": "Lusaka", "country": "Zambia", "latitude": -15.3875, "longitude": 28.3228, "altitude": 1279, "type": "capital"},
    "lilongwe": {"name": "Lilongwe", "country": "Malawi", "latitude": -13.9626, "longitude": 33.7741, "altitude": 1050, "type": "capital"},
    "maputo": {"name": "Maputo", "country": "Mozambique", "latitude": -25.9692, "longitude": 32.5732, "altitude": 47, "type": "capital"},
    "antananarivo": {"name": "Antananarivo", "country": "Madagascar", "latitude": -18.8792, "longitude": 47.5079, "altitude": 1276, "type": "capital"},
    "port louis": {"name": "Port Louis", "country": "Mauritius", "latitude": -20.1609, "longitude": 57.5012, "altitude": 5, "type": "capital"},
    "victoria": {"name": "Victoria", "country": "Seychelles", "latitude": -4.6796, "longitude": 55.4920, "altitude": 3, "type": "capital"},
    
    # Oceania
    "canberra": {"name": "Canberra", "country": "Australia", "latitude": -35.2809, "longitude": 149.1300, "altitude": 577, "type": "capital"},
    "sydney": {"name": "Sydney", "country": "Australia", "latitude": -33.8688, "longitude": 151.2093, "altitude": 3, "type": "major_city"},
    "melbourne": {"name": "Melbourne", "country": "Australia", "latitude": -37.8136, "longitude": 144.9631, "altitude": 31, "type": "major_city"},
    "brisbane": {"name": "Brisbane", "country": "Australia", "latitude": -27.4698, "longitude": 153.0251, "altitude": 27, "type": "major_city"},
    "perth": {"name": "Perth", "country": "Australia", "latitude": -31.9505, "longitude": 115.8605, "altitude": 46, "type": "major_city"},
    "adelaide": {"name": "Adelaide", "country": "Australia", "latitude": -34.9285, "longitude": 138.6007, "altitude": 50, "type": "major_city"},
    "wellington": {"name": "Wellington", "country": "New Zealand", "latitude": -41.2865, "longitude": 174.7762, "altitude": 31, "type": "capital"},
    "auckland": {"name": "Auckland", "country": "New Zealand", "latitude": -36.8485, "longitude": 174.7633, "altitude": 10, "type": "major_city"},
    "suva": {"name": "Suva", "country": "Fiji", "latitude": -18.1248, "longitude": 178.4501, "altitude": 1, "type": "capital"},
    "port moresby": {"name": "Port Moresby", "country": "Papua New Guinea", "latitude": -9.4438, "longitude": 147.1803, "altitude": 35, "type": "capital"},
    "nuku'alofa": {"name": "Nuku'alofa", "country": "Tonga", "latitude": -21.1789, "longitude": -175.1982, "altitude": 1, "type": "capital"},
    "apia": {"name": "Apia", "country": "Samoa", "latitude": -13.8506, "longitude": -171.7513, "altitude": 2, "type": "capital"},
    "port vila": {"name": "Port Vila", "country": "Vanuatu", "latitude": -17.7334, "longitude": 168.3273, "altitude": 1, "type": "capital"},
    "honiara": {"name": "Honiara", "country": "Solomon Islands", "latitude": -9.4280, "longitude": 159.9729, "altitude": 8, "type": "capital"},
    "palikir": {"name": "Palikir", "country": "Micronesia", "latitude": 6.9248, "longitude": 158.1611, "altitude": 92, "type": "capital"},
    "majuro": {"name": "Majuro", "country": "Marshall Islands", "latitude": 7.1315, "longitude": 171.1845, "altitude": 3, "type": "capital"},
    "ngerulmud": {"name": "Ngerulmud", "country": "Palau", "latitude": 7.5006, "longitude": 134.6242, "altitude": 65, "type": "capital"},
    "funafuti": {"name": "Funafuti", "country": "Tuvalu", "latitude": -8.5243, "longitude": 179.1942, "altitude": 2, "type": "capital"},
    "tarawa": {"name": "Tarawa", "country": "Kiribati", "latitude": 1.4518, "longitude": 172.9717, "altitude": 3, "type": "capital"},
    "yaren": {"name": "Yaren", "country": "Nauru", "latitude": -0.5477, "longitude": 166.9209, "altitude": 30, "type": "capital"},
}

def get_city_by_name(city_name: str) -> Optional[Dict]:
    """
    Look up a city by name (case-insensitive).
    
    Args:
        city_name: Name of the city to look up
        
    Returns:
        Dictionary with city information if found, None otherwise
    """
    return WORLD_CITIES.get(city_name.lower().strip())

def search_cities(query: str, limit: int = 10) -> List[Dict]:
    """
    Search for cities that match a query string.
    
    Args:
        query: Search query (case-insensitive)
        limit: Maximum number of results to return
        
    Returns:
        List of matching city dictionaries
    """
    query = query.lower().strip()
    matches = []
    
    for key, city_info in WORLD_CITIES.items():
        if query in key or query in city_info["name"].lower() or query in city_info["country"].lower():
            matches.append(city_info)
            if len(matches) >= limit:
                break
    
    return matches

def get_all_cities() -> Dict[str, Dict]:
    """Return the complete cities database."""
    return WORLD_CITIES

def get_cities_by_country(country: str) -> List[Dict]:
    """
    Get all cities for a specific country.
    
    Args:
        country: Country name or code
        
    Returns:
        List of city dictionaries for the country
    """
    country = country.lower().strip()
    return [city_info for city_info in WORLD_CITIES.values() 
            if country in city_info["country"].lower()]

def get_capitals() -> List[Dict]:
    """Get all capital cities."""
    return [city_info for city_info in WORLD_CITIES.values() 
            if city_info["type"] == "capital"]

def get_major_cities() -> List[Dict]:
    """Get all major cities (non-capitals)."""
    return [city_info for city_info in WORLD_CITIES.values() 
            if city_info["type"] == "major_city"]

# Export the lookup function for easy access
lookup_city = get_city_by_name