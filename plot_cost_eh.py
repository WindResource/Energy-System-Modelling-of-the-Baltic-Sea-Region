import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# Define font parameters
font = {'family': 'serif',
        'weight': 'normal',
        'size': 12}

# Set font
plt.rc('font', **font)

def present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost):
    """
    Calculate the total present value of cable cost.

    Parameters:
        equip_cost (float): Equipment cost.
        inst_cost (float): Installation cost.
        ope_cost_yearly (float): Yearly operational cost.
        deco_cost (float): Decommissioning cost.

    Returns:
        float: Total present value of cost.
    """
    # Define years for installation, operational, and decommissioning
    inst_year = 0  # First year (installation year)
    ope_year = inst_year + 5  # Operational costs start year
    dec_year = ope_year + 25  # Decommissioning year
    end_year = dec_year + 2  # End year

    # Discount rate
    discount_rate = 0.05

    # Initialize total operational cost
    total_ope_cost = 0

    # Adjust cost for each year
    for year in range(inst_year, end_year + 1):
        discount_factor = (1 + discount_rate) ** -year  # Calculate the discount factor for the year
        if year == inst_year:
            equip_cost *= discount_factor  # Discount equipment cost for the installation year
            inst_cost *= discount_factor  # Discount installation cost for the installation year
        elif ope_year <= year < dec_year:
            total_ope_cost += ope_cost_yearly * discount_factor  # Accumulate discounted operational cost for each year
        elif year == dec_year:
            deco_cost *= discount_factor  # Discount decommissioning cost for the decommissioning year

    # Calculate total present value of cost
    total_cost = equip_cost + inst_cost + total_ope_cost + deco_cost

    return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost

def supp_struct_cond(water_depth):
        """
        Determines the support structure type based on water depth.

        Returns:
        - str: Support structure type ('monopile', 'jacket', 'floating', or 'default').
        """
        # Define depth ranges for different support structures
        if water_depth < 120:
            return "jacket"
        elif 120 <= water_depth:
            return "floating"

def equip_cost_lin(water_depth, support_structure, ice_cover, eh_capacity):
    """
    Calculates the energy hub equipment cost based on water depth, capacity, and export cable type.

    Returns:
    - float: Calculated equipment cost.
    """
    # Coefficients for equipment cost calculation based on the support structure and year
    support_structure_coeff = {
        'jacket': (233, 47, 309, 62),
        'floating': (87, 68, 116, 91)
    }

    equip_coeff = (22.87, 7.06)
    
    # Define parameters
    c1, c2, c3, c4 = support_structure_coeff[support_structure]
    
    c5, c6 = equip_coeff
    
    # Define equivalent electrical power
    equiv_capacity = 0.5 * eh_capacity

    # Calculate foundation cost for jacket/floating
    supp_cost = (c1 * water_depth + c2 * 1e3) * equiv_capacity + (c3 * water_depth + c4 * 1e3)
    
    if ice_cover == 1:
        supp_cost *= 1.10  # Increase cost by 10% if ice cover is present
    
    # Power converter cost
    conv_cost = (c5 * 1e3) * eh_capacity + (c6 * 1e6)
    
    return supp_cost, conv_cost

def inst_deco_cost_lin(supp_structure, port_distance, operation):
    """
    Calculate installation or decommissioning cost of offshore substations based on the water depth, and port distance.

    Returns:
    - float: Calculated installation or decommissioning cost.
    """
    # Installation coefficients for different vehicles
    inst_coeff = {
        ('jacket' 'PSIV'): (1, 18.5, 24, 96, 200),
        ('floating','HLCV'): (1, 22.5, 10, 0, 40),
        ('floating','AHV'): (3, 18.5, 30, 90, 40)
    }

    # Decommissioning coefficients for different vehicles
    deco_coeff = {
        ('jacket' 'PSIV'): (1, 18.5, 24, 96, 200),
        ('floating','HLCV'): (1, 22.5, 10, 0, 40),
        ('floating','AHV'): (3, 18.5, 30, 30, 40)
    }

    # Choose the appropriate coefficients based on the operation type
    coeff = inst_coeff if operation == 'inst' else deco_coeff
        
    if supp_structure == 'jacket':
        c1, c2, c3, c4, c5 = coeff[('jacket' 'PSIV')]
        # Calculate installation cost for jacket
        total_cost = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1e3) / 24
    elif supp_structure == 'floating':
        total_cost = 0
        
        # Iterate over the coefficients for floating (HLCV and AHV)
        for vessel_type in [('floating', 'HLCV'), ('floating', 'AHV')]:
            c1, c2, c3, c4, c5 = coeff[vessel_type]
            # Calculate installation cost for the current vessel type
            vessel_cost = ((1 / c1) * ((2 * port_distance) / c2 + c3) + c4) * (c5 * 1e3) / 24
            # Add the cost for the current vessel type to the total cost
            total_cost += vessel_cost
    
    return total_cost

def eh_cost_lin(water_depth, ice_cover, port_distance, eh_capacity):
    """
    """
    
    # Determine support structure
    supp_structure = supp_struct_cond(water_depth)
    
    # Calculate equipment cost
    supp_cost, conv_cost = equip_cost_lin(water_depth, supp_structure, ice_cover, eh_capacity)

    equip_cost = supp_cost + conv_cost
    
    # Calculate installation and decommissioning cost
    inst_cost = inst_deco_cost_lin(supp_structure, port_distance, "inst")
    deco_cost = inst_deco_cost_lin(supp_structure, port_distance, "deco")

    # Calculate yearly operational cost
    ope_cost_yearly = 0.03 * conv_cost
    
    total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = present_value(equip_cost, inst_cost, ope_cost_yearly, deco_cost)  # Calculate present value of cost

    # Convert cost to millions of Euros
    total_cost *= 1e-6
    equip_cost *= 1e-6
    inst_cost *= 1e-6
    total_ope_cost *= 1e-6
    deco_cost *= 1e-6
    
    return total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost

def plot_total_cost_vs_water_depth():
    water_depths = np.linspace(0, 300, 500)
    ice_cover = 0  # Assuming no ice cover for simplicity
    port_distance = 50  # Assuming a constant port distance
    eh_capacity = 1000  # Assuming a constant energy hub capacity of 1GW

    total_costs, equip_costs, inst_costs, total_ope_costs, deco_costs = [], [], [], [], []

    for wd in water_depths:
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = eh_cost_lin(wd, ice_cover, port_distance, eh_capacity)
        total_costs.append(total_cost)
        equip_costs.append(equip_cost)
        inst_costs.append(inst_cost)
        total_ope_costs.append(total_ope_cost)
        deco_costs.append(deco_cost)

    plt.figure(figsize=(7, 5))
    plt.plot(water_depths, total_costs, label='Total PV')
    plt.plot(water_depths, equip_costs, label='Equipment PV')
    plt.plot(water_depths, inst_costs, label='Installation PV')
    plt.plot(water_depths, total_ope_costs, label='Total Operating PV')
    plt.plot(water_depths, deco_costs, label='Decommissioning PV')

    # Set domain and range
    plt.xlim(0, 300)
    plt.ylim(-1, 100)

    # Set the number of major ticks and minor ticks
    x_major_locator = MultipleLocator(50)
    x_minor_locator = MultipleLocator(5)
    y_major_locator = MultipleLocator(25)
    y_minor_locator = MultipleLocator(5)

    # Apply the major and minor tick locators
    plt.gca().xaxis.set_major_locator(x_major_locator)
    plt.gca().xaxis.set_minor_locator(x_minor_locator)
    plt.gca().yaxis.set_major_locator(y_major_locator)
    plt.gca().yaxis.set_minor_locator(y_minor_locator)

    # Add vertical lines for support structure domains
    plt.axvline(x=120, color='grey', linewidth=1.5, linestyle='--')

    # Add vertical text annotations
    plt.text(4, plt.ylim()[1] * 0.05, 'Jacket', rotation=90, verticalalignment='bottom')
    plt.text(124, plt.ylim()[1] * 0.05, 'Floating', rotation=90, verticalalignment='bottom')

    plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
    plt.minorticks_on()

    plt.xlabel('Water Depth (m)')
    plt.ylabel('Cost (M\u20AC)')

    # Position the legend above the figure
    plt.legend(bbox_to_anchor=(0, 1.25), loc='upper left', ncol=2, frameon=False)
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\eh_total_cost_vs_water_depth.png', dpi=400, bbox_inches='tight')
    plt.grid(True)
    plt.show()

def plot_total_cost_vs_capacity(water_depth):
    eh_capacities = np.linspace(250, 2000, 500)  # Energy hub capacities in MW
    ice_cover = 0  # Assuming no ice cover for simplicity
    port_distance = 50  # Assuming a constant port distance

    total_costs, equip_costs, inst_costs, total_ope_costs, deco_costs = [], [], [], [], []

    for eh_capacity in eh_capacities:
        total_cost, equip_cost, inst_cost, total_ope_cost, deco_cost = eh_cost_lin(water_depth, ice_cover, port_distance, eh_capacity)
        total_costs.append(total_cost)
        equip_costs.append(equip_cost)
        inst_costs.append(inst_cost)
        total_ope_costs.append(total_ope_cost)
        deco_costs.append(deco_cost)

    plt.figure(figsize=(7, 5))
    plt.plot(eh_capacities, total_costs, label='Total PV')
    plt.plot(eh_capacities, equip_costs, label='Equipment PV')
    plt.plot(eh_capacities, inst_costs, label='Installation PV')
    plt.plot(eh_capacities, total_ope_costs, label='Total Operating PV')
    plt.plot(eh_capacities, deco_costs, label='Decommissioning PV')

    # Set domain and range
    plt.xlim(250, 2000)
    plt.ylim(0, 175)

    # Set the number of major ticks and minor ticks
    x_major_locator = MultipleLocator(250)
    x_minor_locator = MultipleLocator(25)
    y_major_locator = MultipleLocator(25)
    y_minor_locator = MultipleLocator(5)

    # Apply the major and minor tick locators
    plt.gca().xaxis.set_major_locator(x_major_locator)
    plt.gca().xaxis.set_minor_locator(x_minor_locator)
    plt.gca().yaxis.set_major_locator(y_major_locator)
    plt.gca().yaxis.set_minor_locator(y_minor_locator)

    # Turn on minor ticks
    plt.minorticks_on()

    plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')

    # Add vertical text annotations
    supp_struct_str = 'Jacket' if water_depth < 120 else 'Floating'
    plt.text(275, plt.ylim()[1] * 0.05, supp_struct_str, rotation=90)

    plt.xlabel('Capacity (MW)')
    plt.ylabel('Cost (M\u20AC)')

    # Position the legend above the figure
    plt.legend(bbox_to_anchor=(0, 1.25), loc='upper left', ncol=2, frameon=False)

    plt.grid(True)
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\eh_total_cost_vs_capacity_{supp_struct_str}.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_equip_cost_vs_water_depth():
    water_depths = np.linspace(0, 300, 500)
    ice_cover = 0  # Assuming no ice cover for simplicity
    eh_capacity = 1000  # Assuming a constant energy hub capacity of 1GW

    supp_costs, conv_costs, equip_costs = [], [], []

    for wd in water_depths:
        support_structure = supp_struct_cond(wd)
        supp_cost, conv_cost = equip_cost_lin(wd, support_structure, ice_cover, eh_capacity)
        equip_cost = supp_cost + conv_cost
        supp_costs.append(supp_cost * 1e-6)  # Convert to millions of Euros
        conv_costs.append(conv_cost * 1e-6)  # Convert to millions of Euros
        equip_costs.append(equip_cost * 1e-6)  # Convert to millions of Euros

    plt.figure(figsize=(7, 5))
    plt.plot(water_depths, supp_costs, label='Support Structure Cost')
    plt.plot(water_depths, conv_costs, label='Transformer Cost')
    plt.plot(water_depths, equip_costs, label='Total Equipment Cost')
    
    # Set domain and range
    plt.xlim(0, 300)
    plt.ylim(0, 100)

    # Set the number of major ticks and minor ticks
    x_major_locator = MultipleLocator(50)
    x_minor_locator = MultipleLocator(5)
    y_major_locator = MultipleLocator(25)
    y_minor_locator = MultipleLocator(5)

    # Apply the major and minor tick locators
    plt.gca().xaxis.set_major_locator(x_major_locator)
    plt.gca().xaxis.set_minor_locator(x_minor_locator)
    plt.gca().yaxis.set_major_locator(y_major_locator)
    plt.gca().yaxis.set_minor_locator(y_minor_locator)

    # Add vertical lines for support structure domains
    plt.axvline(x=120, color='grey', linewidth=1.5, linestyle='--')
    
    # Add vertical text annotations
    plt.text(4, plt.ylim()[1] * 0.05, 'Jacket', rotation=90, verticalalignment='bottom')
    plt.text(124, plt.ylim()[1] * 0.05, 'Floating', rotation=90, verticalalignment='bottom')
    
    plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
    plt.minorticks_on()
    
    plt.xlabel('Water Depth (m)')
    plt.ylabel('Cost (M\u20AC)')
    
    # Position the legend above the figure
    plt.legend(bbox_to_anchor=(0, 1.25), loc='upper left', ncol=1, frameon=False)
    
    plt.grid(True)
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\eh_equip_cost_vs_water_depth.png', dpi=400, bbox_inches='tight')
    plt.show()

def plot_inst_deco_cost_vs_port_distance(water_depth):
    port_distances = np.linspace(0, 300, 500)

    inst_costs, deco_costs = [], []

    for pd in port_distances:
        support_structure = supp_struct_cond(water_depth)
        inst_cost = inst_deco_cost_lin(support_structure, pd, "inst")
        deco_cost = inst_deco_cost_lin(support_structure, pd, "deco")
        inst_costs.append(inst_cost * 1e-6)  # Convert to millions of Euros
        deco_costs.append(deco_cost * 1e-6)  # Convert to millions of Euros

    plt.figure(figsize=(7, 5))
    plt.plot(port_distances, inst_costs, label='Installation Cost')
    plt.plot(port_distances, deco_costs, label='Decommissioning Cost')
    
    # Set domain and range
    plt.xlim(0, 300)
    plt.ylim(0, 1.5)

    # Set the number of major ticks and minor ticks
    x_major_locator = MultipleLocator(50)
    x_minor_locator = MultipleLocator(5)
    y_major_locator = MultipleLocator(0.25)
    y_minor_locator = MultipleLocator(0.05)

    # Apply the major and minor tick locators
    plt.gca().xaxis.set_major_locator(x_major_locator)
    plt.gca().xaxis.set_minor_locator(x_minor_locator)
    plt.gca().yaxis.set_major_locator(y_major_locator)
    plt.gca().yaxis.set_minor_locator(y_minor_locator)


    plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
    plt.minorticks_on()

    # Add vertical text annotations
    supp_struct_str = 'Jacket' if water_depth < 120 else 'Floating'
    plt.text(2, plt.ylim()[1] * 0.05, supp_struct_str, rotation=90)
    
    plt.xlabel('Port Distance (km)')
    plt.ylabel('Cost (M\u20AC)')
    
    # Position the legend above the figure
    plt.legend(bbox_to_anchor=(0, 1.2), loc='upper left', ncol=1, frameon=False)
    
    plt.grid(True)
    plt.savefig(f'C:\\Users\\cflde\\Downloads\\eh_inst_deco_cost_vs_port_distance_{supp_struct_str}.png', dpi=400, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    wd_jacket = 50
    wd_floating = 150

    # Call the function to plot the costs

    plot_total_cost_vs_water_depth()

    for wd in (wd_jacket, wd_floating):
        plot_total_cost_vs_capacity(wd)
    
    plot_equip_cost_vs_water_depth()

    for wd in (wd_jacket, wd_floating):
        plot_inst_deco_cost_vs_port_distance(wd)
    
