(function() {
  var D = {"nombre":"MARIANO_SAN_MARINO_FLYER20","comp":{"w":1600,"h":1600,"fps":30,"dur":10},"capas":[{"id":"CAMARA","tipo":"nulo","url":null,"archivo":null,"color":null,"tam":null,"blend":null,"blur_fijo":0,"borde":0.42,"padre":null,"keys":{"scale":[[0,105],[4,100.6,"out"],[10,100,"lin"]],"pos":[[0,[800,806]],[4,[800,801],"out"],[10,[800,800],"lin"]]}},{"id":"FONDO","tipo":"imagen","url":"https://glossary-hazardous-player-implementing.trycloudflare.com/clientes/Mariano/flyersaanimar/capas_flyer_20_05Aug_0251/32_fondo_sin_paneles.png","archivo":"32_fondo_sin_paneles.png","color":null,"tam":null,"blend":null,"blur_fijo":0,"borde":0.42,"padre":"CAMARA","keys":{"opacity":[[0,0],[0.4,100,"out"]],"blur":[[0,26],[0.9,0,"out"]]}},{"id":"PANEL_IZQ","tipo":"imagen","url":"https://glossary-hazardous-player-implementing.trycloudflare.com/clientes/Mariano/flyersaanimar/capas_flyer_20_05Aug_0251/30_panel_izq_limpio.png","archivo":"30_panel_izq_limpio.png","color":null,"tam":null,"blend":null,"blur_fijo":0,"borde":0.42,"padre":"CAMARA","keys":{"opacity":[[0,0],[0.4,100,"out"]],"pos":[[0,[370,830]],[0.95,[800,800],"out"],[10,[788,800],"lin"]],"rot":[[0,-2.5],[0.95,0,"out"]],"scale":[[0,104],[0.95,100,"out"],[10,104,"lin"]]}},{"id":"PANEL_DER","tipo":"imagen","url":"https://glossary-hazardous-player-implementing.trycloudflare.com/clientes/Mariano/flyersaanimar/capas_flyer_20_05Aug_0251/31_panel_der_limpio.png","archivo":"31_panel_der_limpio.png","color":null,"tam":null,"blend":null,"blur_fijo":0,"borde":0.42,"padre":"CAMARA","keys":{"opacity":[[0.12,0],[0.5,100,"out"]],"pos":[[0.12,[1240,820]],[1.1,[800,800],"out"],[10,[814,800],"lin"]],"rot":[[0.12,2.5],[1.1,0,"out"]],"scale":[[0.12,104],[1.1,100,"out"],[10,104,"lin"]]}},{"id":"LOGO","tipo":"imagen","url":"https://glossary-hazardous-player-implementing.trycloudflare.com/clientes/Mariano/flyersaanimar/capas_flyer_20_05Aug_0251/02_bloque_00_14.png","archivo":"02_bloque_00_14.png","color":null,"tam":null,"blend":null,"blur_fijo":0,"borde":0.42,"padre":"CAMARA","keys":{"opacity":[[0.85,0],[1.1,100,"out"]],"pos":[[0.85,[800,610]],[1.4,[800,812],"out"],[1.62,[800,800],"inout"]]}},{"id":"TITULAR","tipo":"imagen","url":"https://glossary-hazardous-player-implementing.trycloudflare.com/clientes/Mariano/flyersaanimar/capas_flyer_20_05Aug_0251/03_bloque_17_32.png","archivo":"03_bloque_17_32.png","color":null,"tam":null,"blend":null,"blur_fijo":0,"borde":0.42,"padre":"CAMARA","keys":{"wipe":[[1.35,100],[2.25,0,"out"]],"pos":[[1.35,[800,826]],[2.25,[800,800],"out"]],"blur":[[1.35,7],[2.1,0,"out"]],"opacity":[[1.35,100]]}},{"id":"PRECIO","tipo":"imagen","url":"https://glossary-hazardous-player-implementing.trycloudflare.com/clientes/Mariano/flyersaanimar/capas_flyer_20_05Aug_0251/04_bloque_71_78.png","archivo":"04_bloque_71_78.png","color":null,"tam":null,"blend":null,"blur_fijo":0,"borde":0.42,"padre":"CAMARA","keys":{"opacity":[[2.25,0],[2.42,100,"out"]],"scale":[[2.25,72],[2.58,106,"out"],[2.8,100,"inout"],[6,100,"lin"],[6.28,104,"out"],[6.6,100,"inout"]]}},{"id":"PIE","tipo":"imagen","url":"https://glossary-hazardous-player-implementing.trycloudflare.com/clientes/Mariano/flyersaanimar/capas_flyer_20_05Aug_0251/05_bloque_93_99.png","archivo":"05_bloque_93_99.png","color":null,"tam":null,"blend":null,"blur_fijo":0,"borde":0.42,"padre":"CAMARA","keys":{"opacity":[[2.95,0],[3.6,100,"out"]]}},{"id":"BRILLO","tipo":"solido","url":null,"archivo":null,"color":[255,255,255],"tam":[220,2600],"blend":"add","blur_fijo":130,"borde":0.42,"padre":null,"keys":{"rot":[[0,18]],"pos":[[4.4,[-380,800]],[6.1,[1980,800],"inout"]],"opacity":[[4.4,0],[4.95,7,"out"],[5.5,7,"lin"],[6.1,0,"in"]]}},{"id":"VINETA","tipo":"vineta","url":null,"archivo":null,"color":null,"tam":null,"blend":null,"blur_fijo":0,"borde":0.45,"padre":null,"keys":{"opacity":[[0,0],[0.9,42,"out"]]}}],"eases":{"lin":{"entra":0.1,"saleAnterior":0.1},"out":{"entra":88,"saleAnterior":12},"in":{"entra":12,"saleAnterior":88},"inout":{"entra":75,"saleAnterior":75}}};
  var log = [];

  // -- Descarga ---------------------------------------------------------------
  // curl existe en macOS y en Windows 10+. Se verifica que el archivo quedo en
  // disco: callSystem no devuelve el codigo de salida de forma confiable.
  function carpetaTrabajo() {
    var f = new Folder(Folder.myDocuments.fsName + "/SeedanceAE/" + D.nombre);
    if (!f.exists) f.create();
    return f;
  }

  function bajar(url, destino) {
    var f = new File(destino);
    if (f.exists && f.length > 1024) return true;
    system.callSystem('curl -L -s -S --max-time 120 -o "' + destino + '" "' + url + '"');
    f = new File(destino);
    return f.exists && f.length > 1024;
  }

  // -- Keyframes --------------------------------------------------------------
  // Cuantas curvas pide setTemporalEaseAtKey. NO es la cantidad de dimensiones
  // del valor: en una propiedad ESPACIAL -Posicion, Punto de anclaje- la curva
  // es UNA sola, porque describe la velocidad a lo largo de la trayectoria, no
  // de cada eje. Pasarle dos revienta con "el conjunto de valores no tiene 1
  // elementos", que suena a que faltan y en realidad sobran.
  function nCurvas(prop, t) {
    if (prop.isSpatial) return 1;
    var v = prop.valueAtTime(t, false);
    return (v instanceof Array) ? v.length : 1;
  }

  function eases(n, influencia) {
    var a = [];
    for (var i = 0; i < n; i++) a.push(new KeyframeEase(0, influencia));
    return a;
  }

  // Si aun asi la cuenta no le cuadra a esta version de AE, se reintenta con una
  // sola curva antes de tirar todo el montaje por un suavizado.
  function curva(prop, idx, n, entra, sale) {
    try {
      prop.setTemporalEaseAtKey(idx, eases(n, entra), eases(n, sale));
    } catch (e1) {
      try { prop.setTemporalEaseAtKey(idx, eases(1, entra), eases(1, sale)); } catch (e2) {}
    }
  }

  function ponerLlaves(prop, llaves, transformar) {
    if (!llaves || !llaves.length) return;
    var i, v;
    for (i = 0; i < llaves.length; i++) {
      v = transformar ? transformar(llaves[i][1]) : llaves[i][1];
      prop.setValueAtTime(llaves[i][0], v);
    }
    // Las curvas se aplican despues de poner todas las llaves: el indice de un
    // keyframe cambia conforme se insertan los siguientes.
    for (i = 0; i < llaves.length; i++) {
      var nombre = (llaves[i].length > 2) ? llaves[i][2] : "lin";
      var e = D.eases[nombre] || D.eases.lin;
      var idx = i + 1;
      var n = nCurvas(prop, llaves[i][0]);
      if (nombre === "lin") {
        prop.setInterpolationTypeAtKey(idx, KeyframeInterpolationType.LINEAR, KeyframeInterpolationType.LINEAR);
        continue;
      }
      prop.setInterpolationTypeAtKey(idx, KeyframeInterpolationType.BEZIER, KeyframeInterpolationType.BEZIER);
      curva(prop, idx, n, e.entra, 0.1);
      if (idx > 1) {
        var nPrev = nCurvas(prop, llaves[i - 1][0]);
        prop.setInterpolationTypeAtKey(idx - 1, KeyframeInterpolationType.BEZIER, KeyframeInterpolationType.BEZIER);
        curva(prop, idx - 1, nPrev, 0.1, e.saleAnterior);
      }
    }
  }

  // Agrega un efecto probando varios matchNames: el desenfoque cambio de nombre
  // interno entre versiones de AE y el viejo ya no existe en las nuevas.
  function efecto(capa, candidatos) {
    var fx = capa.property("ADBE Effect Parade");
    for (var i = 0; i < candidatos.length; i++) {
      if (fx.canAddProperty(candidatos[i])) return fx.addProperty(candidatos[i]);
    }
    return null;
  }

  // -- Montaje ----------------------------------------------------------------
  app.beginUndoGroup("Flyer animado " + D.nombre);
  try {
    var dir = carpetaTrabajo();
    // Si quedo una comp de un intento anterior se borra: reintentar dejaba dos
    // comps con el mismo nombre en el proyecto de Carlos y ninguna terminada.
    for (var q = app.project.items.length; q >= 1; q--) {
      var it = app.project.items[q];
      if (it instanceof CompItem && it.name === D.nombre) it.remove();
    }
    var comp = app.project.items.addComp(D.nombre, D.comp.w, D.comp.h, 1, D.comp.dur, D.comp.fps);
    comp.bgColor = [0, 0, 0];

    var faltaron = [];
    var porId = {};
    for (var i = 0; i < D.capas.length; i++) {
      var c = D.capas[i];
      var capa = null;

      if (c.tipo === "imagen") {
        var ruta = dir.fsName + "/" + c.archivo;
        if (!bajar(c.url, ruta)) { faltaron.push(c.archivo); continue; }
        var io = new ImportOptions(new File(ruta));
        io.importAs = ImportAsType.FOOTAGE;
        var item = app.project.importFile(io);
        capa = comp.layers.add(item);
      } else if (c.tipo === "solido") {
        capa = comp.layers.addSolid([c.color[0] / 255, c.color[1] / 255, c.color[2] / 255],
                                    c.id, c.tam[0], c.tam[1], 1, D.comp.dur);
        if (c.blur_fijo) {
          var bf = efecto(capa, ["ADBE Gaussian Blur 2", "ADBE Gaussian Blur", "ADBE Fast Blur"]);
          if (bf) bf.property(1).setValue(c.blur_fijo);
        }
        if (c.blend === "add") capa.blendingMode = BlendingMode.ADD;
      } else if (c.tipo === "nulo") {
        // El movimiento de camara en un solo sitio: Carlos puede reencuadrar
        // todo el anuncio moviendo este nulo, sin tocar capa por capa.
        capa = comp.layers.addNull(D.comp.dur);
        capa.enabled = false;
      } else if (c.tipo === "vineta") {
        capa = comp.layers.addSolid([1, 1, 1], c.id, D.comp.w, D.comp.h, 1, D.comp.dur);
        var ramp = efecto(capa, ["ADBE Ramp"]);
        if (ramp) {
          ramp.property("ADBE Ramp-0001").setValue([D.comp.w / 2, D.comp.h / 2]);
          ramp.property("ADBE Ramp-0002").setValue([1, 1, 1, 1]);
          ramp.property("ADBE Ramp-0003").setValue([D.comp.w / 2, D.comp.h * (0.5 + c.borde)]);
          ramp.property("ADBE Ramp-0004").setValue([0.30, 0.30, 0.36, 1]);
          ramp.property("ADBE Ramp-0005").setValue(2); // 2 = radial
        }
        capa.blendingMode = BlendingMode.MULTIPLY;
      }
      if (!capa) continue;

      capa.name = c.id;
      porId[c.id] = capa;
      var tr = capa.property("ADBE Transform Group");
      var k = c.keys;

      // El nulo escala alrededor del CENTRO de la comp, no de su propia esquina:
      // AE arma la matriz del padre como T(posicion) . escala . T(-anclaje), asi
      // que poniendo el anclaje en el centro el conjunto se acerca desde el medio.
      if (c.tipo === "nulo") {
        tr.property("ADBE Anchor Point").setValue([D.comp.w / 2, D.comp.h / 2]);
      }

      // setParentWithJump y NO "capa.parent = x": el segundo compensa los valores
      // del hijo para que no se mueva al emparentarlo, y entonces las llaves ya
      // no son las que dice el spec ni las que rindio la revision local.
      if (c.padre && porId[c.padre]) capa.setParentWithJump(porId[c.padre]);

      if (k.pos)     ponerLlaves(tr.property("ADBE Position"), k.pos);
      if (k.scale)   ponerLlaves(tr.property("ADBE Scale"), k.scale, function (v) { return [v, v]; });
      if (k.rot)     ponerLlaves(tr.property("ADBE Rotate Z"), k.rot);
      if (k.opacity) ponerLlaves(tr.property("ADBE Opacity"), k.opacity);

      if (k.blur) {
        var b = efecto(capa, ["ADBE Gaussian Blur 2", "ADBE Gaussian Blur", "ADBE Fast Blur"]);
        if (b) {
          ponerLlaves(b.property(1), k.blur);
          if (b.numProperties >= 3) { try { b.property(3).setValue(true); } catch (e0) {} }
        }
      }

      if (k.wipe) {
        var w = efecto(capa, ["ADBE Linear Wipe"]);
        if (w) {
          w.property("ADBE Linear Wipe-0002").setValue(90);  // angulo: entra por la izquierda
          w.property("ADBE Linear Wipe-0003").setValue(90);  // suavizado del borde
          ponerLlaves(w.property("ADBE Linear Wipe-0001"), k.wipe);
        }
      }

      log.push(c.id);
    }

    comp.openInViewer();
    app.endUndoGroup();
    return JSON.stringify({
      ok: true, comp: comp.name, capas: log, faltaron: faltaron,
      carpeta: dir.fsName, w: comp.width, h: comp.height, dur: comp.duration
    });
  } catch (err) {
    app.endUndoGroup();
    return JSON.stringify({ error: String(err), linea: err.line, hechas: log });
  }
})();