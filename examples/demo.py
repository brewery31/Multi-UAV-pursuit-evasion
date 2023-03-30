import os

from typing import Dict

import hydra
import torch
from omegaconf import OmegaConf
from omni_drones import CONFIG_PATH, init_simulation_app


@hydra.main(version_base=None, config_path=CONFIG_PATH, config_name="config")
def main(cfg):
    OmegaConf.resolve(cfg)
    simulation_app = init_simulation_app(cfg)
    print(OmegaConf.to_yaml(cfg))

    import omni.isaac.core.utils.prims as prim_utils
    import omni_drones.utils.kit as kit_utils
    import omni_drones.utils.scene as scene_utils
    from omni.isaac.core.simulation_context import SimulationContext
    from omni_drones.robots.drone import MultirotorBase

    sim = SimulationContext(
        stage_units_in_meters=1.0,
        physics_dt=0.005,
        rendering_dt=0.005,
        sim_params=cfg.sim,
        backend="torch",
        device=cfg.sim.device,
    )

    drones: Dict[str, MultirotorBase] = {}
    n = 3
    for i, model in enumerate(
        [
            # "Crazyflie",
            # "Firefly",
            # "Hummingbird",
            # "Neo11",
            "Omav"
        ]
    ):
        drones[model] = MultirotorBase.REGISTRY[model]()
        translations = torch.zeros(n, 3)
        translations[:, 0] = i
        translations[:, 1] = torch.arange(n)
        translations[:, 2] = 0.5
        drones[model].spawn(translations=translations)

    scene_utils.design_scene()
    sim.reset()

    for drone in drones.values():
        drone.initialize()
    
    iter = 0
    iter_max = 1000
        
    while simulation_app.is_running():
        while iter < iter_max:
            try:
                if sim.is_stopped():
                    break
                if not sim.is_playing():
                    sim.step(render=not cfg.headless)
                    continue
                for drone in drones.values():
                    actions = drone.action_spec.rand((drone.n,))
                    actions.fill_(0.0)
                    drone.apply_action(actions)
                sim.step()
                iter += 1         
            except KeyboardInterrupt:
                break
        else:
            # reset
            for drone in drones.values():
                pass # TODO: reset drone
            iter = 0

    simulation_app.close()


if __name__ == "__main__":
    main()
