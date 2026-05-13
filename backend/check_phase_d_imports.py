"""Quick import check for Phase D modules."""

from app.core.scheduler import DispatchCost, CostAwareRebalanceStrategy, GreedyThresholdStrategy
from app.core.satisfaction import SatisfactionTracker, StationHealth
from app.models.npc import NPC, NpcPopulation
from app.services.demand_service import CommuteDemandService, RuleBasedDemandService

print("All Phase D imports OK")

# Verify DispatchCost.total()
dc = DispatchCost()
assert dc.total(distance_km=5.0, n_bikes=2) == 10.0 + 5.0*2.0 + 2*0.5
print(f"DispatchCost.total(5km, 2bikes) = {dc.total(5.0, 2)}")

# Verify StationHealth defaults
h = StationHealth(station_id="s1")
assert h.satisfaction == 1.0
print(f"StationHealth.satisfaction default = {h.satisfaction}")

# Verify NPC
npc = NPC(id="npc_0", home_station="s1", work_station="s2")
dest = npc.destination_at(400)  # 06:40 - should be work_station
assert dest == "s2", f"Expected s2, got {dest}"
print(f"NPC morning commute: home={npc.home_station} -> {dest}")

# Verify SatisfactionTracker
tracker = SatisfactionTracker(["s1", "s2"])
tracker.update(inventory={"s1": 0, "s2": 5}, capacity={"s1": 10, "s2": 10})
sat_s1 = tracker.get_health("s1").satisfaction
assert sat_s1 < 1.0, f"Expected decay, got {sat_s1}"
print(f"SatisfactionTracker: s1 sat after empty tick = {sat_s1:.4f}")

print("All assertions passed!")
