function activateOnlineWebSocket(userID) {
    const wsOnlineEndpoint = `ws://${window.location.host}/ws/onlineChecker/${userID}`;
    const onlineSocket = new WebSocket(wsOnlineEndpoint);
}