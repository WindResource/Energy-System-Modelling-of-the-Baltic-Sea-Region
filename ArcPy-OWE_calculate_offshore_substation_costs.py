import arcpy
import numpy as np

def determine_support_structure(water_depth):
    """
    Determines the support structure type based on water depth.

    Returns:
    - str: Support structure type ('monopile', 'jacket', 'floating', or 'default').
    """
    # Define depth ranges for different support structures
    if 0 <= water_depth < 30:
        return "sandisland"
    elif 30 <= water_depth < 150:
        return "jacket"
    elif 150 <= water_depth:
        return "floating"
    else:
        # If water depth is outside specified ranges, assign default support structure
        arcpy.AddWarning(f"Water depth {water_depth} does not fall within specified ranges for support structures. Assigning default support structure.")
        return "default"

def calc_equip_costs(water_depth, oss_capacity, HVC_type="AC"):
    """
    Calculates the offshore substation equipment costs based on water depth, capacity, and export cable type.

    Returns:
    - float: Calculated equipment costs.
    """
    # Coefficients for equipment cost calculation based on the support structure and year
    support_structure_coeff = {
        'sandisland': (3.26, 804, 0, 0),
        'jacket': (233, 47, 309, 62),
        'floating': (87, 68, 116, 91)
    }

    # Get the support structure type based on water depth
    support_structure = determine_support_structure(water_depth)

    # Define parameters
    c1, c2, c3, c4 = support_structure_coeff[support_structure]
    
    # Define equivalent electrical power
    equiv_capacity = 0.5 * oss_capacity if HVC_type == "AC" else oss_capacity

    if support_structure == 'sandisland':
        # Calculate foundation costs for sand island
        area_island = (equiv_capacity * 5)
        slope = 0.75
        r_hub = np.sqrt(area_island/np.pi)
        r_seabed = r_hub + (water_depth + 3) / slope
        volume_island = (1/3) * slope * np.pi * (r_seabed ** 3 - r_hub ** 3)
        
        equip_costs = c1 * volume_island + c2 * area_island
    else:
        # Calculate foundation costs for jacket/floating
        equip_costs = (c1 * water_depth + c2 * 1000) * equiv_capacity + (c3 * water_depth + c4 * 1000)

    return equip_costs

def calc_costs(water_depth, port_distance, oss_capacity, HVC_type = "AC", operation = "inst"):
    """
    Calculate installation or decommissioning costs of offshore substations based on the water depth, and port distance.

    Parameters:
    - water_depth (float): Water depth at the installation site, in meters.
    - port_distance (float): Distance from the installation site to the nearest port, in kilometers.
    - oss_capacity (float): Capacity of the offshore substation, in units.
    - HVC_type (str, optional): Type of high-voltage converter ('AC' or 'DC'). Defaults to 'AC'.
    - operation (str, optional): Type of operation ('inst' for installation or 'deco' for decommissioning). Defaults to 'inst'.

    Returns:
    - float: Calculated installation or decommissioning costs in Euros.
    
    Coefficients:
    - Capacity (u/lift): Capacity of the vessel in units per lift.
    - Speed (km/h): Speed of the vessel in kilometers per hour.
    - Load time (h/lift): Load time per lift in hours per lift.
    - Inst. time (h/u): Installation time per unit in hours per unit.
    - Dayrate (keu/d): Dayrate of the vessel in thousands of euros per day.

    Vessels:
    - SUBV (Self-Unloading Bulk Vessels)
    - SPIV (Self-Propelled Installation Vessel)
    - HLCV (Heavy-Lift Cargo Vessels)
    - AHV (Anchor Handling Vessel)
    
    Notes:
    - The function supports both installation and decommissioning operations.
    - Costs are calculated based on predefined coefficients for different support structures and vessels.
    - If the support structure is unrecognized, the function returns None.
    """
    # Installation coefficients for different vehicles
    inst_coeff = {
        ('sandisland','SUBV'): (20000, 25, 2000, 6000, 15),
        ('jacket' 'PSIV'): (1, 18.5, 24, 96, 200),
        ('floating','HLCV'): (1, 22.5, 10, 0, 40),
        ('floating','AHV'): (3, 18.5, 30, 90, 40)
    }

    # Decommissioning coefficients for different vehicles
    deco_coeff = {
        ('sandisland','SUBV'): (20000, 25, 2000, 6000, 15),
        ('jacket' 'PSIV'): (1, 18.5, 24, 96, 200),
        ('floating','HLCV'): (1, 22.5, 10, 0, 40),
        ('floating','AHV'): (3, 18.5, 30, 30, 40)
    }

    # Choose the appropriate coefficients based on the operation type
    coeff = inst_coeff if operation == 'installation' else deco_coeff

    # Get the support structure type based on water depth
    support_structure = determine_support_structure(water_depth)
    
    if support_structure == 'sandisland':
        c1, c2, c3, c4, c5 = coeff[('jacket' 'PSIV')]
        # Define equivalent electrical power
        equiv_capacity = 0.5 * oss_capacity if HVC_type == "AC" else oss_capacity
        
        # Calculate installation costs for sand island
        area_island = (equiv_capacity * 5)
        slope = 0.75
        r_hub = np.sqrt(area_island/np.pi)
        r_seabed = r_hub + (water_depth + 3) / slope
        volume_island = (1/3) * slope * np.pi * (r_seabed ** 3 - r_hub ** 3)
        
        
        total_costs = (volume_island / c1) * ((2 * port_distance / 1000) / c2) + (volume_island / c3) + (volume_island / c4) * (c5 * 1000) / 24
    elif support_structure == 'jacket':
        c1, c2, c3, c4, c5 = coeff[('jacket' 'PSIV')]
        # Calculate installation costs for jacket
        total_costs = ((1 / c1) * ((2 * port_distance / 1000) / c2 + c3) + c4) * (c5 * 1000) / 24
    elif support_structure == 'floating':
        total_costs = 0
        
        # Iterate over the coefficients for floating (HLCV and AHV)
        for vessel_type in [('floating', 'HLCV'), ('floating', 'AHV')]:
            c1, c2, c3, c4, c5 = coeff[vessel_type]
            
            # Calculate installation costs for the current vessel type
            vessel_costs = ((1 if vessel_type[1] == 'HLCV' else 3) / c1) * ((2 * port_distance / 1000) / c2 + c3) + c4 * (c5 * 1000) / 24
            
            # Add the costs for the current vessel type to the total costs
            total_costs += vessel_costs
    else:
        total_costs = None
        
    return total_costs

def logi_costs(water_depth, port_distance, failure_rate=0.08):
    """
    Calculate logistics time and costs for major wind turbine repairs (part of OPEX) based on water depth, port distance, and failure rate for major wind turbine repairs.
    
    Coefficients:
        - Speed (km/h): Speed of the vessel in kilometers per hour.
        - Repair time (h): Repair time in hours.
        - Dayrate (keu/d): Dayrate of the vessel in thousands of euros per day.
        - Roundtrips: Number of roundtrips for the logistics operation.
    
    Returns:
    - tuple: Logistics time in hours per year and logistics costs in Euros.
    """
    # Logistics coefficients for different vessels
    logi_coeff = {
        'JUV': (18.5, 50, 150, 1),
        'Tug': (7.5, 50, 2.5, 2)
    }

    # Determine support structure based on water depth
    support_structure = determine_support_structure(water_depth).capitalize()

    # Determine logistics vessel based on support structure
    vessel = 'Tug' if support_structure == 'Floating' else 'JUV'

    # Get logistics coefficients for the chosen vessel
    c = logi_coeff[vessel]

    # Calculate logistics time in hours per year
    logistics_time = failure_rate * ((2 * c[3] * port_distance / 1000) / c[0] + c[1])

    # Calculate logistics costs using the provided equation
    logistics_costs = logistics_time * c[3] * 1000 / 24

    return logistics_time, logistics_costs

def update_fields():
    """
    Update the attribute table of the wind turbine coordinates shapefile (WTC) with calculated equipment, installation,
    decommissioning, logistics costs, logistics time, and Opex.

    Returns:
    - None
    """
    
    # Define fields to be added if they don't exist
    fields_to_add = [
        ('SuppStruct', 'TEXT'),
        ('EquiC20', 'DOUBLE'),
        ('EquiC30', 'DOUBLE'),
        ('EquiC50', 'DOUBLE'),
        ('InstC', 'DOUBLE'),
        ('InstT', 'DOUBLE'),
        ('Capex20', 'DOUBLE'),
        ('Capex30', 'DOUBLE'),
        ('Capex50', 'DOUBLE'),
        ('LogiC', 'DOUBLE'),
        ('LogiT', 'DOUBLE'),
        ('Opex20', 'DOUBLE'),
        ('Opex30', 'DOUBLE'),
        ('Opex50', 'DOUBLE'),
        ('Decex', 'DOUBLE'),
        ('DecT', 'DOUBLE'),
    ]
    
    # Function to add a field if it does not exist in the layer
    def add_field_if_not_exists(layer, field_name, field_type):
        if field_name not in [field.name for field in arcpy.ListFields(layer)]:
            arcpy.AddField_management(layer, field_name, field_type)
            arcpy.AddMessage(f"Added field '{field_name}' to the attribute table.")

    # Access the current ArcGIS project
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Find the wind turbine layer in the map
    turbine_layer = next((layer for layer in map.listLayers() if layer.name.startswith('WTC')), None)

    # Check if the turbine layer exists
    if not turbine_layer:
        arcpy.AddError("No layer starting with 'WTC' found in the current map.")
        return

    # Deselect all currently selected features
    arcpy.SelectLayerByAttribute_management(turbine_layer, "CLEAR_SELECTION")
    
    arcpy.AddMessage(f"Processing layer: {turbine_layer.name}")

    # Check if required fields exist in the attribute table
    required_fields = ['WaterDepth', 'Capacity', 'Distance']
    existing_fields = [field.name for field in arcpy.ListFields(turbine_layer)]
    for field in required_fields:
        if field not in existing_fields:
            arcpy.AddError(f"Required field '{field}' is missing in the attribute table.")
            return

    # Add new fields to the attribute table if they do not exist
    for field_name, field_type in fields_to_add:
        add_field_if_not_exists(turbine_layer, field_name, field_type)

    # Get the list of fields in the attribute table
    fields = [field.name for field in arcpy.ListFields(turbine_layer)]

    # Update each row in the attribute table
    with arcpy.da.UpdateCursor(turbine_layer, fields) as cursor:
        for row in cursor:
            # Extract water depth and turbine capacity from the current row
            water_depth = -row[fields.index("WaterDepth")]  # Invert the sign
            turbine_capacity = row[fields.index("Capacity")]

            # Determine support structure and assign it to the corresponding field
            support_structure = determine_support_structure(water_depth).capitalize()
            row[fields.index("SuppStruct")] = support_structure

            # Iterate over each year and calculate costs and time
            for year in ['2020', '2030', '2050']:
                field_name_ec = f"EquiC{year[2:]}"
                field_name_cap = f"Capex{year[2:]}"

                if field_name_ec in fields and field_name_cap in fields:
                    # Calculate equipment costs for the current year
                    equi_costs = calc_equip_costs(water_depth, year, turbine_capacity)
                    row[fields.index(field_name_ec)] = round(equi_costs)

                    # Calculate installation and decommissioning costs and time
                    inst_hours, inst_costs = calc_costs(water_depth, row[fields.index("Distance")],
                                                        turbine_capacity, 'inst')
                    deco_hours, deco_costs = calc_costs(water_depth, row[fields.index("Distance")],
                                                        turbine_capacity, 'deco')

                    # Assign calculated values to the corresponding fields
                    row[fields.index("InstT")] = round(inst_hours)
                    row[fields.index("DecT")] = round(deco_hours)
                    row[fields.index("InstC")] = round(inst_costs)

                    # Calculate and assign total capital expenditure for the current year
                    capex = equi_costs + inst_costs
                    row[fields.index(field_name_cap)] = round(capex)

                    # Assign decommissioning costs if the field exists
                    field_name_dec = "Decex"
                    if field_name_dec in fields:
                        row[fields.index(field_name_dec)] = round(deco_costs)

                    # Calculate and assign logistics costs and time
                    logi_costs_value = logi_costs(water_depth, row[fields.index("Distance")])[1]
                    logi_time = logi_costs(water_depth, row[fields.index("Distance")])[0]

                    row[fields.index("LogiC")] = round(logi_costs_value)
                    row[fields.index("LogiT")] = round(logi_time)

                    # Calculate material costs and assign operating expenses if the field exists
                    material_costs = 0.025 * equi_costs
                    field_name_opex = f"Opex{year[2:]}"
                    if field_name_opex in fields:
                        row[fields.index(field_name_opex)] = round(material_costs + logi_costs_value)

            cursor.updateRow(row)

    arcpy.AddMessage(f"Attribute table of {turbine_layer} updated successfully.")

if __name__ == "__main__":
    update_fields()




