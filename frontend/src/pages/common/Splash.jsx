import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

function Splash() {
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setTimeout(() => {
      navigate("/roles");
    }, 2000);

    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-blue-600 text-white">
      <div className="text-center">

        <div className="text-6xl mb-6">
          🔍
        </div>

        <h1 className="text-4xl font-bold">
          Product Compliance
        </h1>

        <p className="mt-3 text-blue-100">
          Smart Product Verification System
        </p>

        <p className="mt-8 text-sm">
          Loading...
        </p>

      </div>
    </div>
  );
}

export default Splash;