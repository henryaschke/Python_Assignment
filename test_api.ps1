# PowerShell script to test all API endpoints
Write-Host "Testing Energy Trading API Endpoints" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000/api"
$credentials = @{
    email = "admin@example.com"
    password = "admin123"
}

# Helper function to make API calls
function Invoke-ApiCall {
    param (
        [string]$Method,
        [string]$Endpoint,
        [object]$Body = $null,
        [string]$Token = $null
    )
    
    $headers = @{}
    if ($Token) {
        $headers["Authorization"] = "Bearer $Token"
    }

    $params = @{
        Uri = "$baseUrl$Endpoint"
        Method = $Method
        Headers = $headers
        ContentType = "application/json"
    }

    if ($Body -and $Method -ne "GET") {
        $params["Body"] = ($Body | ConvertTo-Json)
    }

    try {
        $response = Invoke-RestMethod @params
        
        # Handle case where response is a JSON string instead of an object
        if ($response -is [string] -and $response.StartsWith('[') -and $response.EndsWith(']')) {
            try {
                $response = $response | ConvertFrom-Json -ErrorAction SilentlyContinue
            } catch {
                Write-Host "Warning: Could not parse response as JSON: $_" -ForegroundColor Yellow
            }
        }
        
        return $response
    }
    catch {
        Write-Host "Error calling $Endpoint" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            Write-Host $_.ErrorDetails.Message -ForegroundColor Red
        }
        return $null
    }
}

# Test status endpoint
Write-Host "`nTesting Status Endpoint:" -ForegroundColor Green
$status = Invoke-ApiCall -Method "GET" -Endpoint "/status"
Write-Host "Status: $($status.status)"
Write-Host "Database connected: $($status.database.connected)"

# Authenticate and get token
Write-Host "`nTesting Authentication:" -ForegroundColor Green
$authResponse = Invoke-ApiCall -Method "POST" -Endpoint "/auth/login" -Body $credentials
if ($authResponse) {
    Write-Host "Authentication successful"
    $token = $authResponse.access_token
    Write-Host "Token received: $($token.Substring(0, 15))..."

    # Test getting user info
    Write-Host "`nTesting User Info:" -ForegroundColor Green
    $userInfo = Invoke-ApiCall -Method "GET" -Endpoint "/auth/me" -Token $token
    Write-Host "User email: $($userInfo.email)"
    Write-Host "User name: $($userInfo.name)"
    
    # Test battery status
    Write-Host "`nTesting Battery Status:" -ForegroundColor Green
    $batteryStatus = Invoke-ApiCall -Method "GET" -Endpoint "/battery/status" -Token $token
    if ($batteryStatus) {
        Write-Host "Current level: $($batteryStatus.level)%"
        Write-Host "Total capacity: $($batteryStatus.capacity.total) kWh"
        Write-Host "Used capacity: $($batteryStatus.capacity.used) kWh"
        Write-Host "Remaining capacity: $($batteryStatus.capacity.remaining) kWh"
        Write-Host "Percentage: $($batteryStatus.capacity.percentage)%"
    }
    
    # Test market data - today
    Write-Host "`nTesting Market Data (Today):" -ForegroundColor Green
    $marketData = Invoke-ApiCall -Method "GET" -Endpoint "/market-data/today" -Token $token
    Write-Host "Retrieved $($marketData.Count) market data entries"
    if ($marketData.Count -gt 0) {
        Write-Host "First entry: Delivery Period: $($marketData[0].delivery_period), Price: $($marketData[0].close)"
    }
    
    # Test market data - current
    Write-Host "`nTesting Market Data (Current):" -ForegroundColor Green
    $currentMarketData = Invoke-ApiCall -Method "GET" -Endpoint "/market-data/current" -Token $token
    if ($currentMarketData) {
        # Different APIs return price in different properties
        $price = if ($currentMarketData.price) { 
            $currentMarketData.price 
        } elseif ($currentMarketData.close) { 
            $currentMarketData.close 
        } elseif ($currentMarketData.close_price) { 
            $currentMarketData.close_price 
        } else { 
            "N/A" 
        }
        
        Write-Host "Current price: $price"
        Write-Host "Delivery period: $($currentMarketData.delivery_period)"
        Write-Host "Status: $($currentMarketData.status)"
        Write-Host "Market: $($currentMarketData.market)"
    }
    
    # Test forecast
    Write-Host "`nTesting Price Forecast:" -ForegroundColor Green
    $forecast = Invoke-ApiCall -Method "GET" -Endpoint "/forecast/price" -Token $token
    if ($forecast) {
        Write-Host "Retrieved $($forecast.Count) forecast entries"
        if ($forecast.Count -gt 0) {
            # Check both possible property names for price
            $priceValue = if ($forecast[0].price) { 
                $forecast[0].price 
            } elseif ($forecast[0].predicted_price) { 
                $forecast[0].predicted_price 
            } else { 
                "N/A" 
            }
            Write-Host "First forecast: Time: $($forecast[0].timestamp), Price: $priceValue"
        }
    }
    
    # Test forecast accuracy
    Write-Host "`nTesting Forecast Accuracy:" -ForegroundColor Green
    $accuracy = Invoke-ApiCall -Method "GET" -Endpoint "/forecast/accuracy" -Token $token
    if ($accuracy) {
        Write-Host "Period: $($accuracy.period)"
        Write-Host "MAPE: $($accuracy.mape)%"
    }

    # Test electricity trading endpoints
    Write-Host "`nTesting Electricity Trading:" -ForegroundColor Green
    
    # First check current battery level
    $batteryBefore = Invoke-ApiCall -Method "GET" -Endpoint "/battery/status" -Token $token
    if ($batteryBefore) {
        Write-Host "Initial battery level: $($batteryBefore.level)%"
        Write-Host "Initial energy: $($batteryBefore.capacity.used) kWh"
        
        # Test buying electricity
        Write-Host "`n  Testing Buy Electricity:" -ForegroundColor Yellow
        $buyRequest = @{
            quantity = 10.0  # Buy 10 kWh
            price = 40.0     # Set a specific price
        }
        $buyResult = Invoke-ApiCall -Method "POST" -Endpoint "/trades/buy" -Body $buyRequest -Token $token
        if ($buyResult) {
            Write-Host "  Buy Status: $($buyResult.success)"
            Write-Host "  Message: $($buyResult.message)"
            Write-Host "  Total Cost: $($buyResult.total_cost)"
            Write-Host "  New Battery Level: $($buyResult.new_battery_level)%"
        }
        
        # Check battery level after buying
        Start-Sleep -Seconds 1  # Wait a moment for the database to update
        $batteryAfterBuy = Invoke-ApiCall -Method "GET" -Endpoint "/battery/status" -Token $token
        if ($batteryAfterBuy) {
            Write-Host "`n  Battery level after buying: $($batteryAfterBuy.level)%"
            Write-Host "  Energy after buying: $($batteryAfterBuy.capacity.used) kWh"
        }
        
        # Test selling electricity
        Write-Host "`n  Testing Sell Electricity:" -ForegroundColor Yellow
        $sellRequest = @{
            quantity = 5.0  # Sell 5 kWh
            price = 45.0    # Set a specific price
        }
        $sellResult = Invoke-ApiCall -Method "POST" -Endpoint "/trades/sell" -Body $sellRequest -Token $token
        if ($sellResult) {
            Write-Host "  Sell Status: $($sellResult.success)"
            Write-Host "  Message: $($sellResult.message)"
            Write-Host "  Total Revenue: $($sellResult.total_revenue)"
            Write-Host "  New Battery Level: $($sellResult.new_battery_level)%"
        }
        
        # Check battery level after selling
        Start-Sleep -Seconds 1  # Wait a moment for the database to update
        $batteryAfterSell = Invoke-ApiCall -Method "GET" -Endpoint "/battery/status" -Token $token
        if ($batteryAfterSell) {
            Write-Host "`n  Battery level after selling: $($batteryAfterSell.level)%"
            Write-Host "  Energy after selling: $($batteryAfterSell.capacity.used) kWh"
        }
        
        # Test trade history endpoint
        Write-Host "`n  Testing Trade History:" -ForegroundColor Yellow
        $tradeHistory = Invoke-ApiCall -Method "GET" -Endpoint "/trades/" -Token $token
        if ($tradeHistory) {
            Write-Host "  Retrieved $($tradeHistory.Count) trade records"
            if ($tradeHistory.Count -gt 0) {
                Write-Host "  Latest trade: Type: $($tradeHistory[0].type), Quantity: $($tradeHistory[0].quantity), Price: $($tradeHistory[0].price), Status: $($tradeHistory[0].status)"
            }
        }
    }

    # Trade History - Get trade history for user
    try {
        Write-Host "`nChecking trade history..." -ForegroundColor Yellow
        $response = Invoke-ApiCall -Method "GET" -Endpoint "/trades/" -Token $token
        
        if ($response.Count -gt 0) {
            $latestTrade = $response[0]
            Write-Host "Trade history retrieved! Found $($response.Count) trade records." -ForegroundColor Green
            Write-Host "Latest trade - Type: $($latestTrade.type), Quantity: $($latestTrade.quantity) kWh, Price: $($latestTrade.price), Status: $($latestTrade.status)" -ForegroundColor Green
        } else {
            Write-Host "No trade records found." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Error retrieving trade history: $_" -ForegroundColor Red
    }

    # Trade Profit/Loss - Calculate profit/loss from executed trades
    try {
        Write-Host "`nChecking trade profit/loss..." -ForegroundColor Yellow
        $response = Invoke-ApiCall -Method "GET" -Endpoint "/performance/trade-pnl" -Token $token
        
        Write-Host "Trade P&L calculation retrieved!" -ForegroundColor Green
        Write-Host "Period: $($response.period.start_date) to $($response.period.end_date)" -ForegroundColor Green
        Write-Host "Trades: $($response.trades.executed) executed out of $($response.trades.total) total" -ForegroundColor Green
        Write-Host "Volume - Buy: $($response.volume.buy) kWh, Sell: $($response.volume.sell) kWh, Net: $($response.volume.net) kWh" -ForegroundColor Green
        Write-Host "Financials:" -ForegroundColor Green
        Write-Host "  - Buy Cost: $($response.financials.buy_cost)" -ForegroundColor Green
        Write-Host "  - Sell Revenue: $($response.financials.sell_revenue)" -ForegroundColor Green
        Write-Host "  - Profit/Loss: $($response.financials.profit_loss)" -ForegroundColor Green
        Write-Host "  - Profit/Loss per kWh: $($response.financials.profit_loss_per_kWh)" -ForegroundColor Green
    } catch {
        Write-Host "Error retrieving trade profit/loss: $_" -ForegroundColor Red
    }
}
else {
    Write-Host "Authentication failed" -ForegroundColor Red
}

Write-Host "`nAPI Testing Complete" -ForegroundColor Cyan