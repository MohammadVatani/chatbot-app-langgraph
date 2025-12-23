import React, { useCallback, useEffect, useMemo, useState } from "react";

const DEFAULT_BASE_URL = "http://localhost:8000";

function Status({ message }) {
  if (!message) return null;
  return (
    <div className={`status status-${message.kind}`}>
      {message.text}
    </div>
  );
}

function OrganizationRow({ org, onDelete }) {
  return (
    <div className="org-row">
      <div className="org-details">
        <div className="org-name">{org.name}</div>
        <div className="org-meta">
          <span>Org ID: {org.org_id}</span>
          <span>Role: {org.role ?? "member"}</span>
        </div>
      </div>
      <div className="org-actions">
        <button className="danger" onClick={() => onDelete(org)}>
          Delete
        </button>
      </div>
    </div>
  );
}

export default function App() {
  const [baseUrl, setBaseUrl] = useState(DEFAULT_BASE_URL);
  const [token, setToken] = useState("");
  const [orgName, setOrgName] = useState("");
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);

  const headers = useMemo(() => {
    const h = { "Content-Type": "application/json" };
    if (token.trim()) {
      h.Authorization = `Bearer ${token.trim()}`;
    }
    return h;
  }, [token]);

  const handleError = useCallback((message) => {
    setStatus({ kind: "error", text: message });
  }, []);

  const parseResponseError = async (response) => {
    let detail = response.statusText || "Request failed";
    try {
      const data = await response.json();
      detail = data?.detail || data?.message || JSON.stringify(data);
    } catch {
      // ignore parsing errors
    }
    return `${detail} (status ${response.status})`;
  };

  const loadOrganizations = useCallback(async () => {
    if (!token.trim()) {
      handleError("Provide a bearer token to fetch organizations.");
      return;
    }

    setLoading(true);
    setStatus(null);
    try {
      const response = await fetch(`${baseUrl}/organizations`, {
        headers,
      });
      if (!response.ok) {
        throw new Error(await parseResponseError(response));
      }
      const data = await response.json();
      setOrganizations(data);
      setStatus({ kind: "success", text: "Organizations loaded." });
    } catch (error) {
      handleError(error.message);
    } finally {
      setLoading(false);
    }
  }, [baseUrl, headers, handleError, token]);

  const createOrganization = async (event) => {
    event.preventDefault();
    if (!orgName.trim()) {
      handleError("Organization name is required.");
      return;
    }
    if (!token.trim()) {
      handleError("Provide a bearer token to create organizations.");
      return;
    }

    setLoading(true);
    setStatus(null);
    try {
      const response = await fetch(`${baseUrl}/organizations`, {
        method: "POST",
        headers,
        body: JSON.stringify({ name: orgName.trim() }),
      });

      if (!response.ok) {
        throw new Error(await parseResponseError(response));
      }

      const created = await response.json();
      const normalized = { ...created, role: "admin" };
      setOrganizations((prev) => [normalized, ...prev]);
      setOrgName("");
      setStatus({
        kind: "success",
        text: `Organization "${created.name}" created.`,
      });
    } catch (error) {
      handleError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const deleteOrganization = async (org) => {
    if (!token.trim()) {
      handleError("Provide a bearer token to delete organizations.");
      return;
    }
    const confirmed = window.confirm(
      `Delete organization "${org.name}"? This action cannot be undone.`
    );
    if (!confirmed) return;

    setLoading(true);
    setStatus(null);
    try {
      const response = await fetch(`${baseUrl}/organizations/${org.org_id}`, {
        method: "DELETE",
        headers,
      });
      if (!response.ok) {
        throw new Error(await parseResponseError(response));
      }
      setOrganizations((prev) =>
        prev.filter((item) => item.org_id !== org.org_id)
      );
      setStatus({
        kind: "success",
        text: `Organization "${org.name}" deleted.`,
      });
    } catch (error) {
      handleError(error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token.trim()) {
      loadOrganizations();
    }
  }, [token, loadOrganizations]);

  return (
    <div className="app">
      <header>
        <div>
          <h1>Organization Admin Panel</h1>
          <p>Manage organizations: create new ones or remove existing ones.</p>
        </div>
        <div className="connection">
          <label>
            API Base URL
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="http://localhost:8000"
            />
          </label>
          <label>
            Bearer Token
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Paste your token"
            />
          </label>
        </div>
      </header>

      <main>
        <Status message={status} />

        <section className="card">
          <h2>Create Organization</h2>
          <form onSubmit={createOrganization} className="form">
            <label>
              Name
              <input
                type="text"
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                placeholder="New organization name"
                disabled={loading}
              />
            </label>
            <button type="submit" disabled={loading}>
              {loading ? "Working..." : "Create"}
            </button>
          </form>
        </section>

        <section className="card">
          <div className="card-header">
            <h2>Organizations</h2>
            <div className="card-actions">
              <button onClick={loadOrganizations} disabled={loading}>
                {loading ? "Loading..." : "Refresh"}
              </button>
            </div>
          </div>
          {organizations.length === 0 ? (
            <p className="empty">No organizations found.</p>
          ) : (
            <div className="org-list">
              {organizations.map((org) => (
                <OrganizationRow
                  key={org.org_id}
                  org={org}
                  onDelete={deleteOrganization}
                />
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
