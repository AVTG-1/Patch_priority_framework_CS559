# Developer A - Quick Reference Card

## Essential Files

```
📁 src/data_model/          ← Your implementation
📁 tests/data_model/         ← Unit tests
📁 config/                   ← Example configurations
📁 docs/                     ← Documentation
📄 tests/integration/sample_export.json  ← For Developer B
```

## Core Classes

```python
# Import everything you need
from data_model import (
    SystemClass, SystemInstance,
    Subsystem, Vulnerability,
    PatchGroup, PlayerBase,
    ConfigLoader, NVDImporter, RiskCalculator
)
```

## Critical Integration Method

```python
# THE method Developer B needs
export_dict = system.export_for_game(
    players=[defender, attacker],
    patch_grouping_method="dependencies"
)
# Returns dict with api_version, system_name, subsystems,
# functional_dependencies, network_topology, weights,
# patch_groups, players
```

## Quick Workflows

### Workflow 1: Load & Export
```python
loader = ConfigLoader()
system = loader.load_system("config/example_system.json")
RiskCalculator().compute_importance(system)
export = system.export_for_game()
```

### Workflow 2: Build from Scratch
```python
system = SystemInstance(
    SystemClass(name="MySystem"),
    [Subsystem(id="s1", name="Component")]
)
system.subsystems[0].add_vulnerability(
    Vulnerability(cve_id="CVE-2024-0001", ...)
)
export = system.export_for_game()
```

### Workflow 3: Enrich with NVD
```python
importer = NVDImporter(api_key="optional")
vulns = importer.import_from_nvd(
    ["CVE-2024-0001"],
    subsystem_id="web"
)
for v in vulns:
    subsystem.add_vulnerability(v)
```

## Testing

```bash
# Run all tests
pytest tests/data_model/

# Specific test
pytest tests/data_model/test_vulnerability.py -v

# With coverage
pytest --cov=src/data_model tests/
```

## Key Validation Rules

✅ CVE IDs must start with "CVE-"  
✅ CVSS scores: 0.0 - 10.0  
✅ Patch costs: ≥ 0  
✅ Player roles: "ATTACKER" or "DEFENDER"  
✅ Matrices: square, size = # subsystems  
✅ No self-dependencies  

## Export Contract Checklist

- [ ] api_version = "1.0.0"
- [ ] All subsystems have importance_score
- [ ] Matrices are JSON lists (not numpy)
- [ ] All IDs are valid strings
- [ ] No null values (except optional team_id)
- [ ] Patch groups have cost/impact
- [ ] Players have role & budget

## Documentation Files

1. **QUICKSTART.md** - Usage examples
2. **MODULE_DOCUMENTATION.md** - Full API reference
3. **INTEGRATION_GUIDE.md** - Contract with Developer B
4. **PROJECT_SUMMARY.md** - Complete overview

## Common Issues & Solutions

**Issue:** "CVE ID must start with CVE-"  
**Fix:** Use format "CVE-YYYY-NNNN"

**Issue:** "Matrix dimensions don't match"  
**Fix:** Ensure subsystem count = matrix size

**Issue:** "jsonschema not found"  
**Fix:** `pip install jsonschema`

**Issue:** "NVD rate limit"  
**Fix:** Add delays or get API key

## Performance Tips

- Calculate importance once, reuse
- Use patch grouping methods strategically
- Cache NVD results if fetching many CVEs
- For large systems (100+ subsystems), monitor convergence

## Next Steps

1. ✅ Review PROJECT_SUMMARY.md
2. ✅ Run tests to verify installation
3. ✅ Try example system export
4. ✅ Share sample_export.json with Developer B
5. ⏭️ Begin integration testing

## Support

See documentation in `docs/` folder or review test files for working examples.
