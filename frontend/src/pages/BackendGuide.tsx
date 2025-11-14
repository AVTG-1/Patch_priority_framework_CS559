import { Link } from 'react-router-dom';
import { ChevronRight, Book, Code, Database, Zap, GitBranch, Calculator } from 'lucide-react';
import Card from '../components/Card';

export default function BackendGuide() {
  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex text-sm text-gray-500">
        <Link to="/dashboard" className="hover:text-gray-700">
          Dashboard
        </Link>
        <ChevronRight className="h-4 w-4 mx-2" />
        <span className="text-gray-900">Backend Architecture Guide</span>
      </nav>

      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <Book className="h-8 w-8 text-indigo-600" />
          <h1 className="text-3xl font-bold text-gray-900">
            Backend Architecture Guide
          </h1>
        </div>
        <p className="text-lg text-gray-600">
          A beginner's guide to understanding the patch prioritization framework backend
        </p>
      </div>

      {/* Overview */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <GitBranch className="h-5 w-5 text-indigo-600" />
          High-Level Overview
        </h2>
        <div className="prose prose-sm max-w-none text-gray-700">
          <p className="mb-4">
            The backend consists of <strong>two main parts</strong>:
          </p>
          <div className="grid md:grid-cols-2 gap-4 mb-4">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <h3 className="font-semibold text-blue-900 mb-2">1. Base Backend (Core Logic)</h3>
              <p className="text-blue-800 text-sm">
                Location: <code className="bg-blue-100 px-1 rounded">/base_backend/src/</code>
              </p>
              <p className="text-blue-800 text-sm mt-2">
                Contains the game-theoretic simulation engine, risk calculators, and core data models.
                This is pure Python logic with no web dependencies.
              </p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <h3 className="font-semibold text-green-900 mb-2">2. Web API (HTTP Interface)</h3>
              <p className="text-green-800 text-sm">
                Location: <code className="bg-green-100 px-1 rounded">/web_api/</code>
              </p>
              <p className="text-green-800 text-sm mt-2">
                FastAPI application that exposes REST endpoints for the frontend.
                Handles authentication, database operations, and bridges to base backend.
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Base Backend Structure */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Code className="h-5 w-5 text-indigo-600" />
          Base Backend Structure
        </h2>

        <div className="space-y-6">
          {/* Data Model */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <Database className="h-4 w-4 text-blue-600" />
              1. Data Model Module (<code className="text-sm bg-gray-100 px-2 py-1 rounded">data_model/</code>)
            </h3>
            <div className="ml-6 space-y-3 text-sm text-gray-700">
              <div className="bg-gray-50 p-3 rounded">
                <p className="font-semibold text-gray-900 mb-1">📄 config_loader.py</p>
                <p><strong>Purpose:</strong> Loads and validates system configurations from JSON/dict</p>
                <p><strong>Key Class:</strong> <code>ConfigLoader</code></p>
                <ul className="list-disc ml-5 mt-2">
                  <li><code>load_from_dict(config)</code> - Parse JSON config into SystemInstance</li>
                  <li><code>load_from_file(path)</code> - Load config from file</li>
                  <li>Uses JSON Schema validation to ensure correct structure</li>
                </ul>
              </div>

              <div className="bg-gray-50 p-3 rounded">
                <p className="font-semibold text-gray-900 mb-1">📄 system.py</p>
                <p><strong>Purpose:</strong> Defines system and subsystem structures</p>
                <p><strong>Key Classes:</strong></p>
                <ul className="list-disc ml-5 mt-2">
                  <li><code>SystemClass</code> - Template/blueprint for a system type</li>
                  <li><code>SystemInstance</code> - Actual system with vulnerabilities and subsystems</li>
                  <li>Builds dependency matrices (functional & topological)</li>
                  <li><code>export_for_game()</code> - Prepares data for game engine</li>
                </ul>
              </div>

              <div className="bg-gray-50 p-3 rounded">
                <p className="font-semibold text-gray-900 mb-1">📄 subsystem.py</p>
                <p><strong>Purpose:</strong> Represents individual components of a system</p>
                <p><strong>Key Class:</strong> <code>Subsystem</code></p>
                <ul className="list-disc ml-5 mt-2">
                  <li>Stores importance score (calculated by RiskCalculator)</li>
                  <li>Tracks vulnerabilities within this subsystem</li>
                  <li>Maintains dependency relationships</li>
                </ul>
              </div>

              <div className="bg-gray-50 p-3 rounded">
                <p className="font-semibold text-gray-900 mb-1">📄 vulnerability.py</p>
                <p><strong>Purpose:</strong> Represents a single vulnerability</p>
                <p><strong>Key Class:</strong> <code>Vulnerability</code></p>
                <ul className="list-disc ml-5 mt-2">
                  <li>CVSS impact & exploitability scores</li>
                  <li>Patch cost and dependencies</li>
                  <li>Subsystem assignment</li>
                </ul>
              </div>

              <div className="bg-gray-50 p-3 rounded">
                <p className="font-semibold text-gray-900 mb-1">📄 risk_calculator.py</p>
                <p><strong>Purpose:</strong> Calculates risk metrics and subsystem importance</p>
                <p><strong>Key Class:</strong> <code>RiskCalculator</code></p>
                <ul className="list-disc ml-5 mt-2">
                  <li><code>compute_importance(system)</code> - PageRank-style algorithm with damping (0.85)</li>
                  <li><code>score_vulnerability(vuln, subsystem)</code> - Risk score for a vulnerability</li>
                  <li><code>rank_vulnerabilities(system)</code> - Sorted list by risk</li>
                  <li>Uses functional dependencies (W matrix) and topology (N matrix)</li>
                </ul>
              </div>

              <div className="bg-gray-50 p-3 rounded">
                <p className="font-semibold text-gray-900 mb-1">📄 patch_group.py</p>
                <p><strong>Purpose:</strong> Groups vulnerabilities for efficient patching</p>
                <p><strong>Key Class:</strong> <code>PatchGroup</code></p>
                <ul className="list-disc ml-5 mt-2">
                  <li>Aggregates related vulnerabilities</li>
                  <li>Total cost and impact calculations</li>
                  <li><code>collapse_by_dependencies()</code> - Groups by dependency chains</li>
                </ul>
              </div>

              <div className="bg-gray-50 p-3 rounded">
                <p className="font-semibold text-gray-900 mb-1">📄 player.py</p>
                <p className="Purpose:</strong> Represents game players (attackers/defenders)</p>
                <p><strong>Key Class:</strong> <code>PlayerBase</code></p>
                <ul className="list-disc ml-5 mt-2">
                  <li><code>create_defender(id, budget)</code> - Factory for defenders</li>
                  <li><code>create_attacker(id, budget)</code> - Factory for attackers</li>
                  <li>Tracks resource budgets and roles</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Game Engine */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <Zap className="h-4 w-4 text-yellow-600" />
              2. Game Engine Module (<code className="text-sm bg-gray-100 px-2 py-1 rounded">game_engine/</code>)
            </h3>
            <div className="ml-6 space-y-3 text-sm text-gray-700">
              <div className="bg-gray-50 p-3 rounded">
                <p className="font-semibold text-gray-900 mb-1">📄 game_state.py</p>
                <p><strong>Purpose:</strong> Manages current game state during simulation</p>
                <p><strong>Key Class:</strong> <code>GameState</code></p>
                <ul className="list-disc ml-5 mt-2">
                  <li><code>load_from_export(data)</code> - Initialize from SystemInstance export</li>
                  <li><code>apply_patch_group(group_id)</code> - Apply patches</li>
                  <li><code>exploit_vulnerabilities(cve_ids)</code> - Record attacks</li>
                  <li><code>calculate_remaining_impact()</code> - Compute current RIS</li>
                  <li>Tracks patched CVEs and exploited vulnerabilities</li>
                </ul>
              </div>

              <div className="bg-gray-50 p-3 rounded">
                <p className="font-semibold text-gray-900 mb-1">📄 simulator.py</p>
                <p><strong>Purpose:</strong> Runs multi-round patch prioritization game</p>
                <p><strong>Key Class:</strong> <code>Simulator</code></p>
                <ul className="list-disc ml-5 mt-2">
                  <li><code>run_simulation()</code> - Execute full simulation</li>
                  <li><code>run_round()</code> - Execute one round with Nash equilibrium</li>
                  <li><code>build_payoff_matrices()</code> - Create game payoff matrices</li>
                  <li>Tracks RIS trajectory, patch schedule, round history</li>
                  <li>Now exports defender_cost and attacker_impact per round</li>
                </ul>
              </div>

              <div className="bg-gray-50 p-3 rounded">
                <p className="font-semibold text-gray-900 mb-1">📄 strategy.py</p>
                <p><strong>Purpose:</strong> Enumerates and manages player strategies</p>
                <p><strong>Key Classes/Functions:</strong></p>
                <ul className="list-disc ml-5 mt-2">
                  <li><code>StrategySet</code> - Set of possible strategies for a player</li>
                  <li><code>enumerate_defender_strategies()</code> - All feasible patch combinations</li>
                  <li><code>enumerate_attacker_strategies()</code> - All feasible exploit combinations</li>
                  <li><code>create_strategy_set(player, patch_groups, vulns)</code> - Factory</li>
                  <li>Limits to max 10 strategies per player for tractability</li>
                </ul>
              </div>

              <div className="bg-gray-50 p-3 rounded">
                <p className="font-semibold text-gray-900 mb-1">📄 nash_solver.py</p>
                <p><strong>Purpose:</strong> Finds Nash equilibrium for two-player games</p>
                <p><strong>Key Class:</strong> <code>NashSolver</code></p>
                <ul className="list-disc ml-5 mt-2">
                  <li>Uses <code>nashpy</code> library for equilibrium computation</li>
                  <li><code>find_pure_equilibria()</code> - Find pure strategy equilibria</li>
                  <li><code>find_mixed_equilibria()</code> - Find mixed strategy equilibria</li>
                  <li><code>find_best_equilibrium()</code> - Select best equilibrium by preference</li>
                  <li>Handles both pure and mixed strategies</li>
                </ul>
              </div>

              <div className="bg-gray-50 p-3 rounded">
                <p className="font-semibold text-gray-900 mb-1">📄 simulation_result.py</p>
                <p><strong>Purpose:</strong> Formats and exports simulation results</p>
                <p><strong>Key Class:</strong> <code>SimulationResult</code></p>
                <ul className="list-disc ml-5 mt-2">
                  <li><code>from_simulation(results)</code> - Parse simulator output</li>
                  <li><code>export_to_dict()</code> - Export as dictionary</li>
                  <li><code>export_to_json(filepath)</code> - Save to file</li>
                  <li>Builds equilibrium report, patch priority list, RIS summary</li>
                  <li>Formats per_round_details with cost and impact</li>
                </ul>
              </div>
            </div>
          </div>

          {/* CLI Runner */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <Calculator className="h-4 w-4 text-purple-600" />
              3. CLI Runner (<code className="text-sm bg-gray-100 px-2 py-1 rounded">cli_runner/</code>)
            </h3>
            <div className="ml-6 space-y-3 text-sm text-gray-700">
              <div className="bg-gray-50 p-3 rounded">
                <p className="font-semibold text-gray-900 mb-1">📄 run_simulation.py</p>
                <p><strong>Purpose:</strong> Standalone CLI tool to run simulations from JSON config</p>
                <p><strong>Usage:</strong></p>
                <pre className="bg-gray-800 text-green-400 p-2 rounded mt-2 text-xs overflow-x-auto">
python run_simulation.py config.json --verbose
                </pre>
                <ul className="list-disc ml-5 mt-2">
                  <li>Loads config from JSON file</li>
                  <li>Creates players from config (multiple defenders/attackers)</li>
                  <li>Runs simulation with base backend</li>
                  <li>Outputs results (verbose or compact JSON)</li>
                  <li>Validation-only mode: <code>--validate</code></li>
                </ul>
              </div>

              <div className="bg-gray-50 p-3 rounded">
                <p className="font-semibold text-gray-900 mb-1">📄 simple_test.json / example_config.json</p>
                <p><strong>Purpose:</strong> Example configuration files</p>
                <p><strong>Contains:</strong></p>
                <ul className="list-disc ml-5 mt-2">
                  <li>System name and subsystems with dependencies</li>
                  <li>Vulnerabilities with CVE IDs, CVSS scores, patch costs</li>
                  <li>Players (defenders and attackers) with budgets</li>
                  <li>Simulation parameters (rounds, grouping method)</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Data Flow */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          📊 Data Flow: From Config to Results
        </h2>
        <div className="space-y-4 text-sm text-gray-700">
          <div className="flex items-center gap-3 p-3 bg-blue-50 rounded border-l-4 border-blue-500">
            <span className="font-bold text-blue-900 text-lg">1</span>
            <div>
              <p className="font-semibold text-blue-900">Configuration</p>
              <p className="text-blue-800">JSON/dict with system, subsystems, vulnerabilities, players</p>
            </div>
          </div>

          <div className="ml-8 text-gray-400">↓</div>

          <div className="flex items-center gap-3 p-3 bg-green-50 rounded border-l-4 border-green-500">
            <span className="font-bold text-green-900 text-lg">2</span>
            <div>
              <p className="font-semibold text-green-900">ConfigLoader</p>
              <p className="text-green-800">Validates and parses into SystemInstance</p>
            </div>
          </div>

          <div className="ml-8 text-gray-400">↓</div>

          <div className="flex items-center gap-3 p-3 bg-purple-50 rounded border-l-4 border-purple-500">
            <span className="font-bold text-purple-900 text-lg">3</span>
            <div>
              <p className="font-semibold text-purple-900">RiskCalculator</p>
              <p className="text-purple-800">Computes subsystem importance scores (PageRank algorithm)</p>
            </div>
          </div>

          <div className="ml-8 text-gray-400">↓</div>

          <div className="flex items-center gap-3 p-3 bg-yellow-50 rounded border-l-4 border-yellow-500">
            <span className="font-bold text-yellow-900 text-lg">4</span>
            <div>
              <p className="font-semibold text-yellow-900">SystemInstance.export_for_game()</p>
              <p className="text-yellow-800">Prepares data for game engine (patch groups, players)</p>
            </div>
          </div>

          <div className="ml-8 text-gray-400">↓</div>

          <div className="flex items-center gap-3 p-3 bg-red-50 rounded border-l-4 border-red-500">
            <span className="font-bold text-red-900 text-lg">5</span>
            <div>
              <p className="font-semibold text-red-900">GameState & Simulator</p>
              <p className="text-red-800">Runs multi-round simulation with Nash equilibrium</p>
            </div>
          </div>

          <div className="ml-8 text-gray-400">↓</div>

          <div className="flex items-center gap-3 p-3 bg-indigo-50 rounded border-l-4 border-indigo-500">
            <span className="font-bold text-indigo-900 text-lg">6</span>
            <div>
              <p className="font-semibold text-indigo-900">SimulationResult</p>
              <p className="text-indigo-800">Formats output: RIS trajectory, patch priority, equilibrium report</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Key Algorithms */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          🧮 Key Algorithms
        </h2>
        <div className="space-y-4">
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <h3 className="font-semibold text-blue-900 mb-2">Subsystem Importance (PageRank)</h3>
            <div className="font-mono text-xs bg-blue-100 p-2 rounded mb-2">
              importance[i] = (1-d)/n + d × (0.6×W.T + 0.4×N.T) @ importance
            </div>
            <p className="text-sm text-blue-800">
              Location: <code>base_backend/src/data_model/risk_calculator.py</code>
            </p>
            <p className="text-sm text-blue-800 mt-1">
              Iteratively computes importance based on dependencies until convergence.
            </p>
          </div>

          <div className="bg-green-50 p-4 rounded-lg border border-green-200">
            <h3 className="font-semibold text-green-900 mb-2">RIS Calculation</h3>
            <div className="font-mono text-xs bg-green-100 p-2 rounded mb-2">
              RIS = Σ (CVSS Impact × Subsystem Importance × Exploit Multiplier)
            </div>
            <p className="text-sm text-green-800">
              Location: <code>base_backend/src/game_engine/game_state.py</code>
            </p>
            <p className="text-sm text-green-800 mt-1">
              Method: <code>calculate_remaining_impact()</code>
            </p>
          </div>

          <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
            <h3 className="font-semibold text-purple-900 mb-2">Nash Equilibrium</h3>
            <div className="font-mono text-xs bg-purple-100 p-2 rounded mb-2">
              Uses nashpy library to solve for equilibria in payoff matrices
            </div>
            <p className="text-sm text-purple-800">
              Location: <code>base_backend/src/game_engine/nash_solver.py</code>
            </p>
            <p className="text-sm text-purple-800 mt-1">
              Finds strategy profiles where no player can improve by changing strategy alone.
            </p>
          </div>
        </div>
      </Card>

      {/* Getting Started */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          🚀 Getting Started with the Code
        </h2>
        <div className="space-y-4 text-sm text-gray-700">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">1. Install Dependencies</h3>
            <pre className="bg-gray-800 text-green-400 p-3 rounded overflow-x-auto">
cd base_backend
pip install -r requirements.txt
            </pre>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 mb-2">2. Run a Simple Simulation (CLI)</h3>
            <pre className="bg-gray-800 text-green-400 p-3 rounded overflow-x-auto">
cd base_backend/cli_runner
python run_simulation.py simple_test.json --verbose
            </pre>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 mb-2">3. Explore the Code</h3>
            <ul className="list-disc ml-5 space-y-1">
              <li>Start with <code>cli_runner/run_simulation.py</code> to see the full flow</li>
              <li>Read <code>data_model/config_loader.py</code> to understand JSON schema</li>
              <li>Check <code>game_engine/simulator.py</code> for simulation logic</li>
              <li>Examine test configs in <code>cli_runner/*.json</code></li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 mb-2">4. Modify and Experiment</h3>
            <ul className="list-disc ml-5 space-y-1">
              <li>Edit JSON configs to test different scenarios</li>
              <li>Adjust weights in <code>risk_calculator.py</code> (functional vs topological)</li>
              <li>Change damping factor (default 0.85) for importance calculation</li>
              <li>Modify payoff formulas in <code>simulator.py</code></li>
            </ul>
          </div>
        </div>
      </Card>

      {/* Back to top */}
      <div className="text-center">
        <button
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          className="text-indigo-600 hover:text-indigo-800 font-medium"
        >
          ↑ Back to Top
        </button>
      </div>
    </div>
  );
}
