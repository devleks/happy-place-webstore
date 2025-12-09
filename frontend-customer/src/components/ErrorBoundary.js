import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to an error reporting service
    console.error('Error caught by boundary:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo
    });

    // You can also log to external service like Sentry
    // Sentry.captureException(error, { contexts: { react: { componentStack: errorInfo.componentStack } } });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      // Fallback UI
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          padding: '20px',
          textAlign: 'center',
          backgroundColor: '#f9f9f9'
        }}>
          <div style={{
            maxWidth: '600px',
            backgroundColor: 'white',
            padding: '40px',
            borderRadius: '8px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
          }}>
            <h1 style={{
              fontSize: '2rem',
              color: '#D4AF37',
              marginBottom: '20px',
              fontWeight: '300',
              letterSpacing: '2px'
            }}>
              Oops! Something went wrong
            </h1>
            
            <p style={{
              fontSize: '1rem',
              color: '#666',
              marginBottom: '30px',
              lineHeight: '1.6'
            }}>
              We're sorry for the inconvenience. An unexpected error occurred while loading this page.
            </p>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details style={{
                marginBottom: '30px',
                textAlign: 'left',
                backgroundColor: '#f5f5f5',
                padding: '15px',
                borderRadius: '4px',
                fontSize: '0.875rem',
                color: '#666'
              }}>
                <summary style={{ cursor: 'pointer', fontWeight: '500', marginBottom: '10px' }}>
                  Error Details (Development Mode)
                </summary>
                <pre style={{
                  overflow: 'auto',
                  maxHeight: '200px',
                  fontSize: '0.75rem',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word'
                }}>
                  {this.state.error.toString()}
                  {'\n\n'}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}

            <div style={{ display: 'flex', gap: '15px', justifyContent: 'center' }}>
              <button
                onClick={this.handleReset}
                style={{
                  padding: '12px 30px',
                  backgroundColor: '#D4AF37',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '1rem',
                  fontWeight: '300',
                  letterSpacing: '1px',
                  cursor: 'pointer',
                  transition: 'background-color 0.3s'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#C5A028'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#D4AF37'}
              >
                Return to Home
              </button>

              <button
                onClick={() => window.location.reload()}
                style={{
                  padding: '12px 30px',
                  backgroundColor: '#f5f5f5',
                  color: '#666',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '1rem',
                  fontWeight: '300',
                  letterSpacing: '1px',
                  cursor: 'pointer',
                  transition: 'background-color 0.3s'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#e5e5e5'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#f5f5f5'}
              >
                Reload Page
              </button>
            </div>

            <p style={{
              marginTop: '30px',
              fontSize: '0.875rem',
              color: '#999'
            }}>
              If the problem persists, please contact our support team.
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
