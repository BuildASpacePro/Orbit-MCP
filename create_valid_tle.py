#!/usr/bin/env python3
"""Create valid TLE data with correct checksums."""

def calculate_checksum(line):
    """Calculate TLE checksum."""
    checksum = 0
    for char in line[:-1]:  # Exclude the checksum digit itself
        if char.isdigit():
            checksum += int(char)
        elif char == '-':
            checksum += 1
    return checksum % 10

# Base TLE lines without checksums
line1_base = "1 25544U 98067A   24001.12345678  .00001234  00000-0  12345-4 0  999"
line2_base = "2 25544  51.6400 123.4567 0001234  12.3456 347.6543 15.4891999912345"

# Calculate checksums
checksum1 = calculate_checksum(line1_base + "0")  # Add dummy checksum
checksum2 = calculate_checksum(line2_base + "0")  # Add dummy checksum

# Create final lines with correct checksums
line1_final = line1_base + str(checksum1)
line2_final = line2_base + str(checksum2)

print("Valid ISS TLE:")
print(f'    "line1": "{line1_final}",')
print(f'    "line2": "{line2_final}",')

# Verify checksums
print(f"\nVerification:")
print(f"Line 1 checksum: {calculate_checksum(line1_final)} (should match {line1_final[-1]})")
print(f"Line 2 checksum: {calculate_checksum(line2_final)} (should match {line2_final[-1]})")