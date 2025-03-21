// Simple helper for making authenticated API calls
function makeApiCall(url, method = 'GET', data = null) {
    // Try to get the token from localStorage
    const token = localStorage.getItem('auth_token');
    
    // Prepare headers
    const headers = {
        'Content-Type': 'application/json'
    };
    
    // Add authorization header if token exists
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Prepare fetch options
    const options = {
        method: method,
        headers: headers
    };
    
    // Add body for non-GET requests if data provided
    if (method !== 'GET' && data) {
        options.body = JSON.stringify(data);
    }
    
    // Make the API call
    return fetch(url, options)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status}`);
            }
            return response.json();
        });
} 