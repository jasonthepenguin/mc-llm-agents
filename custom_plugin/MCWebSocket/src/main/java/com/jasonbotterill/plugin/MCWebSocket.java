package com.jasonbotterill.plugin;

import org.bukkit.Bukkit;
import org.bukkit.plugin.java.JavaPlugin;
import java.net.InetSocketAddress;
import java.util.logging.Logger;
import org.java_websocket.server.WebSocketServer;
import org.java_websocket.handshake.ClientHandshake;
import org.java_websocket.WebSocket;

import java.nio.charset.StandardCharsets;

public class MCWebSocket extends JavaPlugin {

    private WebSocketServer server;
    private static Logger logger;

    @Override
    public void onEnable() {
        logger = this.getLogger();
        startWebSocketServer();
    }

    @Override
    public void onDisable() {
        stopWebSocketServer();
    }

    private void startWebSocketServer() {
        server = new WebSocketServer(new InetSocketAddress("localhost", 8765)) {
            @Override
            public void onOpen(WebSocket conn, ClientHandshake handshake) {
                logger.info("New connection from " + conn.getRemoteSocketAddress());
                conn.send("Hello from Minecraft server!");
            }

            @Override
            public void onClose(WebSocket conn, int code, String reason, boolean remote) {
                logger.info("Connection closed: " + conn.getRemoteSocketAddress());
            }

            @Override
            public void onMessage(WebSocket conn, String message) {
                logger.info("Received: " + message);
                Bukkit.getScheduler().runTask(getPlugin(MCWebSocket.class), () -> {
                    Bukkit.broadcastMessage("[WebSocket] " + message);
                });
            }

            @Override
            public void onError(WebSocket conn, Exception ex) {
                ex.printStackTrace();
            }

            @Override
            public void onStart() {
                logger.info("WebSocket server started on port 8765");
            }
        };
        server.start();
    }

    private void stopWebSocketServer() {
        if (server != null) {
            try {
                server.stop();
                logger.info("WebSocket server stopped.");
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }
}