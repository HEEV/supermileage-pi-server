class SimulationHandler:
    """
    Processes simulation data from the mqtt connection.

    Args:
        new_sim_data(list[dict]): the current simulation data from the mqtt connection
    """

    def __init__(self, new_sim_data: list[dict] = None):
        self._sim_data = new_sim_data

    def set_sim_data(self, new_sim_data: list[dict]):
        """
        Updates the simulation data.

        Args:
            new_sim_data (list[dict]): the new simulation data from the mqtt connection
        """
        self._sim_data = new_sim_data

    def get_sim_data(self) -> dict:
        """
        Retrieves the current simulation data.

        Returns:
            dict: A dictionary containing the current simulation data.
        """
        new_sim_data = {}
        new_sim_data["current_lap"] = self._sim_data
        return new_sim_data
