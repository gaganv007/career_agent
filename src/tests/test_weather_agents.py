from agents.weather_agent import get_weather

def test_weather_agent():
    print(get_weather("New York"))
    print(get_weather("Paris"))