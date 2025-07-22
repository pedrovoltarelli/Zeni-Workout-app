import React from "react";
import Login from "../components/Login"; // Ajuste o caminho conforme sua estrutura

const LoginPage = () => {
  return (
    <div className="login-page">
      <header>
        <h1>Zeni Workout App</h1>
        <p>Faça login para continuar</p>
      </header>

      <main>
        <Login />
      </main>

      <footer>
        <p>&copy; {new Date().getFullYear()} Zeni. Todos os direitos reservados.</p>
      </footer>
    </div>
  );
};

export default LoginPage;
