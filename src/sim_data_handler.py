
"""
Processes simulation data from the mqtt connection.

"""
class Simulation_Handler:
    def __init__(self, new_sim_data = None):
        self.sim_data = new_sim_data

    def set_sim_data(self, new_sim_data):
        self.sim_data = new_sim_data

    def get_sim_data(self):
        return self.sim_data