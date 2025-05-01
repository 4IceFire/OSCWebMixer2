// plugins/auth.js
const fs      = require("fs");
const path    = require("path");
const bcrypt  = require("bcrypt");
const session = require("express-session");

class AuthPlugin {
  constructor() {
    this.users = JSON.parse(
      fs.readFileSync(path.join(__dirname, "auth.json"), "utf8")
    );
  }

  init(app, wss) {
    // 1) Session middleware
    app.use(session({
      secret: "really-long-random-secret",
      resave: false,
      saveUninitialized: false
    }));

    // 2) Login form
    app.get("/login", (req, res) => {
      res.sendFile(path.join(__dirname, "../web/login.html"));
    });
    app.post("/login", (req, res) => {
      const { username, password } = req.body;
      const user = this.users.find(u => u.username === username);
      if (!user || !bcrypt.compareSync(password, user.hash))
        return res.redirect("/login?error=1");
      req.session.user = { username, allowedAux: user.aux };
      res.redirect("/mixer.html");
    });

    // 3) Whitelist static/UI/bootstrap routes
    app.use((req, res, next) => {
      const open = [
        "/login", "/login.html",
        "/mixer.js", "/mixer.css",
        "/config", "/aux"
      ];
      if (open.some(p => req.path.startsWith(p)) || req.session.user)
        return next();
      res.redirect("/login");
    });

    // 4) Reject WS upgrades without a valid session
    wss.on("connection", (socket, req) => {
      if (!req.session || !req.session.user) socket.close();
    });
  }

  handleOSC(msg, { socket }) {
    // Block any Aux-level changes from unauthorized users
    if (
      socket &&
      msg.address.match(/^\/Aux_Outputs\/(\d+)\/Buss_Trim\/level$/)
    ) {
      const auxNum = parseInt(msg.address.split("/")[2], 10);
      if (!socket.request.session.user.allowedAux.includes(auxNum))
        return false;  // drop it
    }
    // otherwise, do nothing and let it pass
  }
}

module.exports = AuthPlugin;
