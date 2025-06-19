# Task One
I need the Docker files to be in the project root directory so if a user clones this repo, it's easier to boot it up. Please update the README.md for the project once this is done. 

# Task Two
We do not need the calculate_access_events function, so please remove (no InfluxDB interfaces needed). The calculate_access_windows tool should return all the access windows between a satellite and a target location at a given time. Also important is that the tool returns:
+ The lighting conditions at the target location (see https://rhodesmill.org/skyfield/examples.html#when-will-it-get-dark-tonight) during culmunation (middle of the access window)
+ The lighting conditions for the satellite during the middle of the access window (https://rhodesmill.org/skyfield/earth-satellites.html#find-when-a-satellite-is-in-sunlight)

# Task Three
It should be possible that if the user provides the MCP server with a list of target locations and a list of satellites, that it can loop through all of them, computing access windows between each satellite and each ground station. 

