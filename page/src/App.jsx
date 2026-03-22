import { useState } from 'react';
import './App.css';
import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
} from 'amazon-cognito-identity-js';

const userPool = new CognitoUserPool({
  UserPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID,
  ClientId: import.meta.env.VITE_COGNITO_CLIENT_ID,
});

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
const apiPath = import.meta.env.VITE_API_PATH || '/';

function App() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [jwt, setJwt] = useState(null);
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState(null);
  const [apiLoading, setApiLoading] = useState(false);
  const [apiResult, setApiResult] = useState(null);
  const [apiError, setApiError] = useState(null);
  const [query, setQuery] = useState('');

  const handleLogin = () => {
    setLoginLoading(true);
    setLoginError(null);

    const authDetails = new AuthenticationDetails({
      Username: username,
      Password: password,
    });

    const user = new CognitoUser({
      Username: username,
      Pool: userPool,
    });

    user.authenticateUser(authDetails, {
      onSuccess: (session) => {
        setJwt(session.getIdToken().getJwtToken());
        setLoginLoading(false);
      },
      onFailure: (err) => {
        setLoginError(err?.message || 'Login failed');
        setJwt(null);
        setLoginLoading(false);
      },
    });
  };

  const handleLogout = () => {
    const user = userPool.getCurrentUser();
    if (user) user.signOut();

    setJwt(null);
    setApiResult(null);
    setApiError(null);
    setQuery('');
  };

  const handleCallApi = async () => {
    if (!jwt || !query) return;

    setApiLoading(true);
    setApiResult(null);
    setApiError(null);

    try {
      const res = await fetch(`${apiBaseUrl}${apiPath}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${jwt}`,
        },
        body: JSON.stringify({ query }),
      });

      const raw = await res.json();

      // Handle API Gateway wrapped lambda responses
      const parsed =
        raw && typeof raw.body === 'string'
          ? JSON.parse(raw.body)
          : raw;

      if (!res.ok) {
        setApiError(parsed?.error || `API error (${res.status})`);
      } else {
        setApiResult(parsed);
      }
    } catch (err) {
      setApiError(err?.message || 'Failed to call API');
    } finally {
      setApiLoading(false);
    }
  };

  return (
    <div className="app-container">
      <h1 className="title">AI SQL Query System</h1>

      <div className="dashboard">
        {/* LEFT PANEL */}
        <div className="left-panel">
          <div className="card-section">
            <h2>Login</h2>

            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input"
            />

            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
            />

            {loginError && <p className="error">{loginError}</p>}

            {!jwt ? (
              <button
                onClick={handleLogin}
                disabled={loginLoading}
                className="btn primary"
              >
                {loginLoading ? 'Logging in…' : 'Login'}
              </button>
            ) : (
              <button onClick={handleLogout} className="btn logout">
                Logout
              </button>
            )}
          </div>

          <div className="card-section">
            <h2>Ask Database</h2>

            <textarea
              placeholder="e.g. Show top 5 players by value"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="textarea"
            />

            <button
              onClick={handleCallApi}
              disabled={!jwt || apiLoading}
              className="btn success"
            >
              {apiLoading ? 'Processing…' : 'Run Query'}
            </button>
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div className="right-panel">
          {apiError && <p className="error">{apiError}</p>}

          {apiResult && (
            <>
              {/* Generated SQL */}
              {apiResult.generated_sql && (
                <>
                  <h3>Generated SQL</h3>
                  <pre className="sql-box">
                    {apiResult.generated_sql}
                  </pre>
                </>
              )}

              {/* Table */}
              {apiResult.db_response?.success &&
                apiResult.db_response?.data && (
                  <>
                    <h3>
                      Results (
                      {apiResult.db_response.data.length} rows)
                    </h3>

                    {apiResult.db_response.data.length === 0 ? (
                      <p>No rows found.</p>
                    ) : (
                      <div className="table-wrapper">
                        <table>
                          <thead>
                            <tr>
                              {Object.keys(
                                apiResult.db_response.data[0]
                              ).map((col) => (
                                <th key={col}>{col}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {apiResult.db_response.data.map(
                              (row, i) => (
                                <tr key={i}>
                                  {Object.values(row).map(
                                    (val, idx) => (
                                      <td key={idx}>
                                        {val !== null
                                          ? val.toString()
                                          : 'NULL'}
                                      </td>
                                    )
                                  )}
                                </tr>
                              )
                            )}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </>
                )}
            </>
          )}

          {!apiResult && (
            <div className="empty-state">
              Run a query to see results here.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;