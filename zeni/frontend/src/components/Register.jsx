import React, { useState } from "react";

const Register = () => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErro("");
    setSucesso("");

    try {
      const res = await fetch("http://localhost:8001/api/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name, email, password }),
      });

      if (res.ok) {
        const data = await res.json();
        setSucesso("Cadastro realizado com sucesso!");
        console.log("Usuário cadastrado:", data);
        // Você pode redirecionar para login aqui, se quiser
      } else {
        const errorData = await res.json();
        setErro(errorData.detail || "Erro no cadastro");
      }
    } catch (err) {
      setErro("Erro de rede. Verifique a API.");
      console.error("Erro no cadastro:", err);
    }
  };

  return (
    <div className="register-container">
      <h2>Criar Conta</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Nome completo"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />

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

        <button type="submit">Cadastrar</button>
      </form>
    </div>
  );
};

export default Register;
