// Mapas: Google Maps (si hay API key en el servidor) o Leaflet con mapa oscuro como respaldo.
// Pines con forma de gota por severidad, ruta con brillo, inicio (verde) y vehículo/fin (azul con halo).

function pinSvg(color, atenuado) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="34" height="44" viewBox="0 0 34 44">
    <path d="M17 42.5C17 42.5 3 27.3 3 16.6A14 14 0 0 1 31 16.6C31 27.3 17 42.5 17 42.5Z" fill="${color}" stroke="#fff" stroke-width="2.4" opacity="${atenuado ? 0.5 : 1}"/>
    <circle cx="17" cy="16.5" r="5.2" fill="#fff"/></svg>`;
  return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
}

const Mapas = {
  _motor: null,

  motor() {
    if (this._motor) return this._motor;
    this._motor = (async () => {
      let clave = "";
      try { clave = (await api("/api/config")).google_maps_key; } catch {}
      if (!clave) return "leaflet";
      try {
        await new Promise((ok, falla) => {
          window.__vsGoogleListo = ok;
          window.gm_authFailure = () => { this._fallaGoogle = true; };
          const s = document.createElement("script");
          s.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(clave)}&callback=__vsGoogleListo&language=es&region=EC`;
          s.onerror = falla;
          document.head.append(s);
        });
        return "google";
      } catch { return "leaflet"; }
    })();
    return this._motor;
  },

  /** Crea un mapa en `el`. alClic(dano) al pulsar un pin; etiquetas: muestra el código (D-102) bajo cada pin. */
  async crear(el, { alClic, etiquetas = false } = {}) {
    const motor = (await this.motor()) === "google" && !this._fallaGoogle ? "google" : "leaflet";
    return motor === "google" ? this._google(el, alClic, etiquetas) : this._leaflet(el, alClic, etiquetas);
  },

  _leaflet(el, alClic, etiquetas) {
    const m = L.map(el, { zoomControl: true, attributionControl: true }).setView([-1.6, -78.4], 7);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      maxZoom: 20, attribution: '&copy; OpenStreetMap &copy; CARTO',
    }).addTo(m);
    const capa = L.layerGroup().addTo(m), capaRuta = L.layerGroup().addTo(m), marcas = new Map();
    let auto = null;
    const circulo = (lat, lon, color, halo) => L.layerGroup([
      ...(halo ? [L.circleMarker([lat, lon], { radius: 18, stroke: false, fillColor: color, fillOpacity: 0.28 })] : []),
      L.circleMarker([lat, lon], { radius: 9, color: "#fff", weight: 3, fillColor: color, fillOpacity: 1 }),
    ]);
    return {
      motor: "OpenStreetMap",
      vehiculo(lat, lon, seguir) {
        if (lat == null) { auto?.remove(); auto = null; return; }
        auto?.remove();
        auto = circulo(lat, lon, "#2f7bf6", true).addTo(m);
        if (seguir) m.panTo([lat, lon], { animate: true });
      },
      marcar(danos) {
        capa.clearLayers(); marcas.clear();
        danos.filter(d => d.lat != null).forEach(d => {
          const icono = L.divIcon({
            className: "pin-vs", iconSize: [34, 44], iconAnchor: [17, 44],
            html: `<img src="${pinSvg(colorSev(d.severidad), d.estado === "reparado")}" alt="">${etiquetas ? `<span class="pin-etq">${esc(d.codigo)}</span>` : ""}`,
          });
          const mk = L.marker([d.lat, d.lon], { icon: icono, title: `${d.codigo} · ${Fmt.tipo(d.tipo)}` }).addTo(capa);
          mk.on("click", () => alClic?.(d));
          marcas.set(d.id, mk);
        });
      },
      ruta(puntos, { fin = true } = {}) {
        capaRuta.clearLayers();
        if (puntos.length < 2) return;
        const ll = puntos.map(p => [p.lat, p.lon]);
        L.polyline(ll, { color: "#2f7bf6", weight: 16, opacity: 0.22, lineCap: "round" }).addTo(capaRuta);
        L.polyline(ll, { color: "#2f7bf6", weight: 5, opacity: 1, lineCap: "round" }).addTo(capaRuta);
        circulo(...ll[0], "#3fb950", false).addTo(capaRuta);
        if (fin) circulo(...ll[ll.length - 1], "#2f7bf6", true).addTo(capaRuta);
      },
      encuadrar(puntos) {
        const p = puntos.filter(x => x.lat != null);
        if (!p.length) return;
        if (p.length === 1) m.setView([p[0].lat, p[0].lon], 17);
        else m.fitBounds(p.map(x => [x.lat, x.lon]), { padding: [60, 60], maxZoom: 18 });
      },
      enfocar(d) { if (d?.lat != null) m.setView([d.lat, d.lon], 18); },
      ajustar() { m.invalidateSize(); },
      destruir() { m.remove(); },
    };
  },

  _google(el, alClic, etiquetas) {
    const oscuro = [
      { elementType: "geometry", stylers: [{ color: "#1f2329" }] },
      { elementType: "labels.text.stroke", stylers: [{ color: "#1f2329" }] },
      { elementType: "labels.text.fill", stylers: [{ color: "#8f98a3" }] },
      { featureType: "road", elementType: "geometry", stylers: [{ color: "#353b45" }] },
      { featureType: "road", elementType: "geometry.stroke", stylers: [{ color: "#1a1d22" }] },
      { featureType: "road.highway", elementType: "geometry", stylers: [{ color: "#4a4f58" }] },
      { featureType: "water", elementType: "geometry", stylers: [{ color: "#1b3352" }] },
      { featureType: "poi.park", elementType: "geometry", stylers: [{ color: "#1d3a26" }] },
      { featureType: "poi.park", elementType: "labels.text.fill", stylers: [{ color: "#5f9e6e" }] },
      { featureType: "poi", elementType: "labels.icon", stylers: [{ visibility: "off" }] },
      { featureType: "poi.business", stylers: [{ visibility: "off" }] },
      { featureType: "transit", stylers: [{ visibility: "off" }] },
    ];
    const m = new google.maps.Map(el, {
      center: { lat: -1.6, lng: -78.4 }, zoom: 7, styles: oscuro, mapTypeControl: false, streetViewControl: true,
      fullscreenControl: false,
    });
    const marcas = new Map();
    let rutaObjs = [], auto = [];
    const circulo = (lat, lon, color, halo) => [
      ...(halo ? [new google.maps.Marker({ map: m, position: { lat, lng: lon }, clickable: false, zIndex: 900,
        icon: { path: google.maps.SymbolPath.CIRCLE, scale: 18, fillColor: color, fillOpacity: 0.28, strokeWeight: 0 } })] : []),
      new google.maps.Marker({ map: m, position: { lat, lng: lon }, clickable: false, zIndex: 901,
        icon: { path: google.maps.SymbolPath.CIRCLE, scale: 9, fillColor: color, fillOpacity: 1, strokeColor: "#fff", strokeWeight: 3 } }),
    ];
    const quitar = lista => lista.forEach(o => o.setMap(null));
    return {
      motor: "Google Maps",
      vehiculo(lat, lon, seguir) {
        quitar(auto);
        auto = lat == null ? [] : circulo(lat, lon, "#2f7bf6", true);
        if (lat != null && seguir) m.panTo({ lat, lng: lon });
      },
      marcar(danos) {
        marcas.forEach(mk => mk.setMap(null)); marcas.clear();
        danos.filter(d => d.lat != null).forEach(d => {
          const mk = new google.maps.Marker({
            position: { lat: d.lat, lng: d.lon }, map: m, title: `${d.codigo} · ${Fmt.tipo(d.tipo)}`, zIndex: 950,
            icon: { url: pinSvg(colorSev(d.severidad), d.estado === "reparado"), scaledSize: new google.maps.Size(34, 44),
                    anchor: new google.maps.Point(17, 44), labelOrigin: new google.maps.Point(17, 56) },
            label: etiquetas ? { text: d.codigo, className: "pin-etq", color: "#fff", fontSize: "11px", fontWeight: "700" } : null,
          });
          mk.addListener("click", () => alClic?.(d));
          marcas.set(d.id, mk);
        });
      },
      ruta(puntos, { fin = true } = {}) {
        quitar(rutaObjs);
        rutaObjs = [];
        if (puntos.length < 2) return;
        const path = puntos.map(p => ({ lat: p.lat, lng: p.lon }));
        rutaObjs.push(new google.maps.Polyline({ path, map: m, strokeColor: "#2f7bf6", strokeWeight: 16, strokeOpacity: 0.22, clickable: false }));
        rutaObjs.push(new google.maps.Polyline({ path, map: m, strokeColor: "#2f7bf6", strokeWeight: 5, strokeOpacity: 1, clickable: false }));
        rutaObjs.push(...circulo(path[0].lat, path[0].lng, "#3fb950", false));
        if (fin) rutaObjs.push(...circulo(path[path.length - 1].lat, path[path.length - 1].lng, "#2f7bf6", true));
      },
      encuadrar(puntos) {
        const p = puntos.filter(x => x.lat != null);
        if (!p.length) return;
        if (p.length === 1) { m.setCenter({ lat: p[0].lat, lng: p[0].lon }); m.setZoom(17); return; }
        const b = new google.maps.LatLngBounds();
        p.forEach(x => b.extend({ lat: x.lat, lng: x.lon }));
        m.fitBounds(b, 70);
        google.maps.event.addListenerOnce(m, "idle", () => { if (m.getZoom() > 18) m.setZoom(18); });
      },
      enfocar(d) { if (d?.lat != null) { m.panTo({ lat: d.lat, lng: d.lon }); m.setZoom(18); } },
      ajustar() {},
      destruir() { marcas.forEach(mk => mk.setMap(null)); el.innerHTML = ""; },
    };
  },
};
