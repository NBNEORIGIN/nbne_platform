fetch("http://localhost:3000/api/auth", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username: "owner@salon-x.demo", password: "admin123" })
})
.then(r => r.text())
.then(t => console.log("RESPONSE:", t))
.catch(e => console.error("ERROR:", e));
