export class MendClient {
  constructor(baseUrl = "") {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  async _get(path) {
    const response = await fetch(this.baseUrl + path);
    if (!response.ok) {
      throw new Error(`Mend API ${response.status}: ${await response.text()}`);
    }
    return response.json();
  }

  status() {
    return this._get("/api/status");
  }

  fcg() {
    return this._get("/api/fcg");
  }

  breakpoint() {
    return this._get("/api/breakpoint");
  }

  dataset() {
    return this._get("/api/dataset");
  }

  runDemo(purpose = "research") {
    if (!["research", "treatment"].includes(purpose)) {
      throw new Error("purpose must be research or treatment");
    }
    return this._get("/api/demo?purpose=" + encodeURIComponent(purpose));
  }
}
