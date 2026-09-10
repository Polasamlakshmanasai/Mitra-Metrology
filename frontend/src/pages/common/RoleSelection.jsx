import { useNavigate } from "react-router-dom";

function RoleSelection() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center px-6">

      <div className="w-full max-w-5xl">

        <div className="text-center mb-12">

          <div className="text-5xl mb-5">
            ⚖️
          </div>

          <h1 className="text-4xl md:text-5xl font-bold">
            MITRA METROLOGY
          </h1>

          <p className="mt-4 text-slate-400 text-lg">
            Smart Product Verification & Inspection System
          </p>

          <p className="mt-2 text-slate-500">
            Select your role to continue
          </p>

        </div>

        <div className="grid md:grid-cols-2 gap-8">

          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 hover:border-blue-500 transition">

            <div className="text-5xl mb-6">
              👤
            </div>

            <h2 className="text-2xl font-bold">
              User
            </h2>

            <p className="text-slate-400 mt-3">
              Verify products, view compliance results,
              track scan history and submit complaints.
            </p>

            <button
              onClick={() => navigate("/user/login")}
              className="mt-7 w-full bg-blue-600 hover:bg-blue-500 py-3 rounded-xl font-semibold transition"
            >
              Continue as User →
            </button>

          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 hover:border-emerald-500 transition">

            <div className="text-5xl mb-6">
              🧑‍💼
            </div>

            <h2 className="text-2xl font-bold">
              Officer
            </h2>

            <p className="text-slate-400 mt-3">
              Perform product inspections, upload evidence,
              submit inspection reports and track history.
            </p>

            <button
              onClick={() => navigate("/officer/login")}
              className="mt-7 w-full bg-emerald-600 hover:bg-emerald-500 py-3 rounded-xl font-semibold transition"
            >
              Continue as Officer →
            </button>

          </div>

        </div>

        <p className="text-center text-slate-500 mt-10">
          Secure • Accurate • Transparent
        </p>

      </div>

    </div>
  );
}

export default RoleSelection;