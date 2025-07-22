import React, { useState } from "react";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErro("");
    setSucesso("");

    try {
      const res = await fetch("http://localhost:8001/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      if (res.ok) {
        const data = await res.json();
        setSucesso("Login realizado com sucesso!");
        console.log("Usuário:", data);
        // redirecione ou salve o ID do usuário aqui
      } else {
        const errorData = await res.json();
        setErro(errorData.detail || "Erro no login");
      }
    } catch (err) {
      setErro("Erro de rede. Verifique a API.");
      console.error("Erro no login:", err);
    }
  };

  return (
    <div className="login-container">
      <h2>Bem-vindo de volta!</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <input
          type="password"
          placeholder="Senha"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        {erro && <div className="erro">{erro}</div>}
        {sucesso && <div className="sucesso">{sucesso}</div>}

        <button type="submit">Entrar</button>
      </form>
    </div>
  );
};

export default Login;
