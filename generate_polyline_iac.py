import arcpy
import networkx as nx
import os
from math import radians, sin, cos, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth surface.
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    r = 6371 * 1e3 # Radius of Earth in meters
    distance = r * c  

    return round(distance)

def create_and_add_inter_array_cables():
    """
    Creates an inter-array cable layout connecting wind turbines to a substation,
    and adds the resulting feature layer with polyline features and corresponding attributes to the current project map.
    Also, updates the substation layer with the total capacity of each wind farm.
    """

    # Example user inputs
    output_fc = "C:\\Users\\cflde\\Documents\\Graduation Project\\ArcGIS Pro\\BalticSea\\Results\\IAC_BalticSea.shp"
    turbine_capacity = 15  # Capacity of each wind turbine in megawatts (MW)
    spatial_ref = arcpy.SpatialReference(4326)  # WGS 1984

    # Get the current map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    map = aprx.activeMap

    # Find the wind turbine layer in the map
    turbine_layer = next((layer for layer in map.listLayers() if layer.name.startswith('WTC')), None)

    # Check if the turbine layer exists
    if not turbine_layer:
        arcpy.AddError("No layer starting with 'WTC' found in the current map.")
        return

    # Find the wind farm coordinate layer in the map
    substation_layer = next((layer for layer in map.listLayers() if layer.name.startswith('OSSC')), None)

    # Check if the substation layer exists
    if not substation_layer:
        arcpy.AddError("No layer starting with 'OSSC' found in the current map.")
        return

    # Check if the Capacity field exists in the substation layer, add it if not
    field_names = [field.name for field in arcpy.ListFields(substation_layer)]
    if "Capacity" not in field_names:
        arcpy.AddField_management(substation_layer, "Capacity", "DOUBLE")
        print("Added 'Capacity' field to substation layer.")

    # Create an empty feature class for the cables
    arcpy.CreateFeatureclass_management(os.path.dirname(output_fc), os.path.basename(output_fc), "POLYLINE", spatial_reference=spatial_ref)

    # Add necessary fields for cable distance, connected capacity, and WF_ID
    arcpy.AddFields_management(output_fc, [
        ["WF_ID", "DOUBLE"],
        ["Distance", "DOUBLE"],
        ["Capacity", "DOUBLE"]
    ])

    # Insert cursor for the new feature class
    cursor = arcpy.da.InsertCursor(output_fc, ["SHAPE@", "WF_ID", "Distance", "Capacity"])

    # Create a dictionary to store total capacities for each substation
    substation_capacities = {}

    # Get unique WF_IDs from the turbine layer
    wf_ids = set(row[0] for row in arcpy.da.SearchCursor(turbine_layer, ["WF_ID"]))

    for wf_id in wf_ids:
        # Get turbine and substation coordinates for the current WF_ID
        turbine_points = [row[0] for row in arcpy.da.SearchCursor(turbine_layer, ["SHAPE@XY"], f"WF_ID = {wf_id}")]
        substation_points = [row[0] for row in arcpy.da.SearchCursor(substation_layer, ["SHAPE@XY"], f"WF_ID = {wf_id}")]

        if not turbine_points:
            arcpy.AddWarning(f"No turbines found for WF_ID '{wf_id}'. Skipping...")
            continue

        if not substation_points:
            arcpy.AddWarning(f"No substation found for WF_ID '{wf_id}'. Skipping...")
            continue

        substation_point = substation_points[0]

        # Create a graph and add nodes for each turbine
        G = nx.Graph()
        for i, point in enumerate(turbine_points):
            G.add_node(i, pos=point)

        # Add edges with weights (Haversine distances) between all turbines
        for i in range(len(turbine_points)):
            for j in range(i + 1, len(turbine_points)):
                dist = haversine(turbine_points[i][1], turbine_points[i][0], turbine_points[j][1], turbine_points[j][0])
                G.add_edge(i, j, weight=dist)

        # Compute the Minimum Spanning Tree
        mst = nx.minimum_spanning_tree(G)

        # Calculate total wind farm capacity
        total_wind_farm_capacity = turbine_capacity * len(turbine_points)
        
        # Store the total capacity for the substation
        substation_capacities[wf_id] = total_wind_farm_capacity

        # Traverse the MST to add cable sections and sum capacities correctly
        def accumulate_capacity(G, node, parent=None):
            total_capacity = turbine_capacity
            for neighbor in G.neighbors(node):
                if neighbor == parent:
                    continue
                edge_data = G.get_edge_data(node, neighbor)
                dist = edge_data['weight']
                array = arcpy.Array([arcpy.Point(*G.nodes[node]['pos']), arcpy.Point(*G.nodes[neighbor]['pos'])])
                polyline = arcpy.Polyline(array, spatial_ref)
                child_capacity = accumulate_capacity(G, neighbor, node)
                cursor.insertRow([polyline, wf_id, dist, child_capacity])
                total_capacity += child_capacity
            return total_capacity

        # Find the closest turbine to the substation and add the connection
        min_dist = float('inf')
        closest_turbine = None
        for i, point in enumerate(turbine_points):
            dist = haversine(substation_point[1], substation_point[0], point[1], point[0])
            if dist < min_dist:
                min_dist = dist
                closest_turbine = i

        array = arcpy.Array([arcpy.Point(*substation_point), arcpy.Point(*turbine_points[closest_turbine])])
        polyline = arcpy.Polyline(array, spatial_ref)
        cursor.insertRow([polyline, wf_id, min_dist, total_wind_farm_capacity])

        # Accumulate capacity for the rest of the MST
        accumulate_capacity(mst, closest_turbine)

    # Cleanup
    del cursor

    print("Inter-array cable layout created.")

    # Add the inter-array cables layer to the map
    map.addDataFromPath(output_fc)
    print(f"Added layer to map: {output_fc}")

    # Update the substation layer with the total capacities
    with arcpy.da.UpdateCursor(substation_layer, ["WF_ID", "Capacity"]) as cursor:
        for row in cursor:
            wf_id = row[0]
            if wf_id in substation_capacities:
                row[1] = substation_capacities[wf_id]
                cursor.updateRow(row)

    print("Substation capacities updated.")

if __name__ == "__main__":
    create_and_add_inter_array_cables()
