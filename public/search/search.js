/* --- SearchName · cliente da busca por nickname --- */
(function () {
  "use strict";

  var form = document.getElementById("form");
  var input = document.getElementById("nick");
  var select = document.getElementById("region");
  var button = document.getElementById("submit");
  var label = document.getElementById("submit-label");
  var hint = document.getElementById("hint");
  var result = document.getElementById("result");
  var players = document.getElementById("players");
  var errorBox = document.getElementById("error");
  var errorTitle = document.getElementById("error-title");
  var errorText = document.getElementById("error-text");

  var t = {
    kicker: document.getElementById("status-kicker"),
    badge: document.getElementById("status-badge"),
    query: document.getElementById("r-query"),
    region: document.getElementById("r-region"),
    time: document.getElementById("r-time"),
    total: document.getElementById("r-total"),
    note: document.getElementById("result-note")
  };

  /* --- endereço da API: mesma origem no Render, Render no Pages, local no PC. --- */
  var API = (function () {
    if (location.protocol === "file:") return "http://127.0.0.1:5000";
    if (/^(localhost|127\.0\.0\.1)$/.test(location.hostname)) return "http://127.0.0.1:5000";
    if (/\.github\.io$/.test(location.hostname)) return "https://searchname-ff.onrender.com";
    return "";
  })();

  function setHint(msg, isError) {
    hint.textContent = msg;
    hint.classList.toggle("is-error", !!isError);
  }

  function reset() {
    result.hidden = true;
    errorBox.hidden = true;
    players.innerHTML = "";
  }

  function showError(title, msg) {
    reset();
    errorTitle.textContent = title;
    errorText.textContent = msg;
    errorBox.hidden = false;
  }

  /* --- botão de copiar o UID de uma conta. --- */
  function botaoCopiar(uid) {
    var botao = document.createElement("button");
    botao.type = "button";
    botao.className = "sn-copy";
    botao.textContent = "copiar";

    botao.addEventListener("click", function () {
      var marcar = function () {
        botao.textContent = "copiado";
        botao.classList.add("is-done");
        setTimeout(function () {
          botao.textContent = "copiar";
          botao.classList.remove("is-done");
        }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(String(uid)).then(marcar).catch(marcar);
      } else {
        marcar();
      }
    });
    return botao;
  }

  /* --- monta uma linha da tabela de resultados. --- */
  function criarLinha(jogador, indice) {
    var linha = document.createElement("div");
    linha.className = "sn-table__row sn-player";

    var nick = document.createElement("span");
    nick.className = "sn-table__nick";
    nick.appendChild(document.createTextNode(jogador.nickname || "(sem nickname)"));

    var sub = document.createElement("small");
    sub.textContent = "conta " + (indice + 1 < 10 ? "0" : "") + (indice + 1);
    nick.appendChild(sub);

    var uid = document.createElement("span");
    uid.className = "sn-table__uid";
    uid.textContent = jogador.uid || "—";

    var nivel = document.createElement("span");
    nivel.className = "sn-table__num";
    nivel.textContent = jogador.level === undefined || jogador.level === null ? "—" : String(jogador.level);

    linha.appendChild(nick);
    linha.appendChild(uid);
    linha.appendChild(nivel);
    linha.appendChild(botaoCopiar(jogador.uid));
    return linha;
  }

  function mostrarResultado(dados) {
    reset();
    var lista = dados.results || [];
    var achou = lista.length > 0;

    t.kicker.textContent = "resultado · " + (dados.region || select.value);
    t.badge.textContent = achou ? lista.length + (lista.length === 1 ? " conta" : " contas") : "vazio";
    t.query.textContent = dados.query || input.value.trim();
    t.region.textContent = dados.region || select.value;
    t.time.textContent = (dados.elapsed_ms || 0) + " ms";
    t.total.textContent = String(lista.length);
    t.note.textContent = achou
      ? "Nickname não é único: confira o UID antes de usar o resultado."
      : "Nenhuma conta combinou com esse nome nessa região. Tente menos caracteres ou outra região.";

    if (achou) {
      lista.forEach(function (jogador, i) {
        players.appendChild(criarLinha(jogador, i));
      });
    } else {
      var vazio = document.createElement("div");
      vazio.className = "sn-table__row is-empty";
      vazio.textContent = "sem contas para \"" + (dados.query || input.value.trim()) + "\" em " + (dados.region || select.value);
      players.appendChild(vazio);
    }

    result.hidden = false;
    result.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function consultar(nome, regiao) {
    var url = API + "/search?name=" + encodeURIComponent(nome) + "&server_name=" + encodeURIComponent(regiao);
    return fetch(url, { headers: { Accept: "application/json" } })
      .then(function (resp) {
        return resp.json().then(function (body) {
          return { ok: resp.ok, status: resp.status, body: body };
        });
      })
      .then(function (r) {
        if (!r.ok) {
          var err = new Error((r.body && r.body.error) || "Falha na busca.");
          err.status = r.status;
          throw err;
        }
        return r.body;
      });
  }

  function buscar(nome, regiao) {
    try { localStorage.setItem("searchname:region", regiao); } catch (e) {}

    setHint("Buscando no servidor…", false);
    button.disabled = true;
    label.textContent = "Buscando";
    reset();

    consultar(nome, regiao)
      .then(function (dados) {
        mostrarResultado(dados);
        setHint("Busca concluída.", false);
      })
      .catch(function (err) {
        var msg = (err && err.message) || "Falha na busca.";
        if (err && err.status === 429) {
          showError("Muitas buscas", "Aguarde um minuto e tente de novo.");
        } else if (err && err.status === 400) {
          showError("Consulta inválida", msg);
        } else if (err && err.status === 502) {
          showError("Servidor não respondeu", msg + " Tente de novo em alguns segundos.");
        } else {
          showError("Não foi possível buscar", msg);
        }
        setHint("Falha na busca.", true);
      })
      .finally(function () {
        button.disabled = false;
        label.textContent = "Buscar";
      });
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    var nome = input.value.trim();
    var regiao = select.value;

    if (nome.length < 3) {
      setHint("Digite pelo menos 3 caracteres do nickname.", true);
      input.focus();
      return;
    }
    buscar(nome, regiao);
  });

  input.addEventListener("input", function () {
    setHint("Mínimo de 3 caracteres. Acentos e símbolos contam.", false);
  });

  /* --- lembra a última região usada. --- */
  try {
    var salva = localStorage.getItem("searchname:region");
    if (salva && select.querySelector('option[value="' + salva + '"]')) select.value = salva;
  } catch (e) {}

  /* --- veio da landing? (?name=&region=) já busca. --- */
  var params = new URLSearchParams(location.search);
  var nomeUrl = (params.get("name") || "").trim();
  var regiaoUrl = (params.get("region") || "").trim().toUpperCase();

  if (regiaoUrl && select.querySelector('option[value="' + regiaoUrl + '"]')) {
    select.value = regiaoUrl;
  }
  if (nomeUrl) {
    input.value = nomeUrl;
    if (nomeUrl.length >= 3) buscar(nomeUrl, select.value);
  }
})();
