import React from "react";
import Register from "../components/Register"; // Ajuste o caminho se necessário

const RegisterPage = () => {
  return (
    <div className="register-page">
      <header>
        <h1>Crie sua conta</h1>
        <p>Comece agora com o Zeni Workout App</p>
      </header>

      <main>
        <Register />
      </main>

      <footer>
        <p>&copy; {new Date().getFullYear()} Zeni. Todos os direitos reservados.</p>
      </footer>
    </div>
  );
};

export default RegisterPage;
