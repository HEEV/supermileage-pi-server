
"""
Processes simulation data from the mqtt connection.

"""
class Simulation_Handler:
    def __init__(self, new_sim_data: list[dict] = None):
        self.sim_data = new_sim_data

    def set_sim_data(self, new_sim_data: list[dict]):
        self.sim_data = new_sim_data

    def get_sim_data(self) -> dict:
        new_sim_data = {}
        new_sim_data["current_lap"] = self.sim_data
        return new_sim_data