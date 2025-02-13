package com.jasonbotterill.plugin;

import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.entity.Player;
import org.bukkit.plugin.java.JavaPlugin;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

import java.net.InetSocketAddress;
import java.util.logging.Logger;
import org.java_websocket.server.WebSocketServer;
import org.java_websocket.handshake.ClientHandshake;
import org.java_websocket.WebSocket;
import org.bukkit.block.Block;
import org.bukkit.block.BlockState;
import org.bukkit.block.data.Openable;
import org.bukkit.block.data.BlockData;
import java.util.HashSet;
import java.util.Set;

public class MCWebSocket extends JavaPlugin {

    private WebSocketServer server;
    private static Logger logger;
    private JSONParser parser;
    private final Set<WebSocket> activeConnections = new HashSet<>();

    @Override
    public void onEnable() {
        logger = this.getLogger();
        parser = new JSONParser();
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
                activeConnections.add(conn);
                conn.send("Connected to Minecraft server");
            }

            @Override
            public void onClose(WebSocket conn, int code, String reason, boolean remote) {
                logger.info("Connection closed: " + conn.getRemoteSocketAddress());
                activeConnections.remove(conn);
            }

            @Override
            public void onMessage(WebSocket conn, String message) {
                try {
                    if (!activeConnections.contains(conn)) {
                        logger.warning("Received message from inactive connection");
                        return;
                    }

                    JSONObject json = (JSONObject) parser.parse(message);
                    String command = (String) json.get("command");
                    JSONObject params = (JSONObject) json.get("params");
                    
                    Bukkit.getScheduler().runTask(getPlugin(MCWebSocket.class), () -> {
                        try {
                            handleCommand(command, params);
                            if (activeConnections.contains(conn) && conn.isOpen()) {
                                conn.send("Command executed: " + command);
                            }
                        } catch (Exception e) {
                            logger.warning("Error executing command: " + e.getMessage());
                            if (activeConnections.contains(conn) && conn.isOpen()) {
                                conn.send("Error executing command: " + e.getMessage());
                            }
                        }
                    });
                } catch (ParseException e) {
                    logger.warning("Failed to parse message: " + e.getMessage());
                    if (conn.isOpen()) {
                        conn.send("Error: Invalid command format");
                    }
                }
            }

            @Override
            public void onError(WebSocket conn, Exception ex) {
                logger.warning("WebSocket error: " + ex.getMessage());
                activeConnections.remove(conn);
            }

            @Override
            public void onStart() {
                logger.info("WebSocket server started on port 8765");
            }
        };
        server.setConnectionLostTimeout(30);
        server.start();
    }

    private void handleCommand(String command, JSONObject params) {
        // Get the first player (or you could specify a player name in params)
        Player player = Bukkit.getOnlinePlayers().iterator().next();
        if (player == null) return;

        Location loc = player.getLocation();
        float yaw = loc.getYaw();
        float pitch = loc.getPitch();

        switch (command) {
            case "move_forward":
                double distance = ((Number) params.get("distance")).doubleValue();
                double rad = Math.toRadians(yaw);
                double dx = -Math.sin(rad) * distance;
                double dz = Math.cos(rad) * distance;
                loc.add(dx, 0, dz);
                player.teleport(loc);
                break;

            case "look_left":
                float leftDegrees = ((Number) params.get("degrees")).floatValue();
                loc.setYaw(yaw - leftDegrees);
                player.teleport(loc);
                break;

            case "look_right":
                float rightDegrees = ((Number) params.get("degrees")).floatValue();
                loc.setYaw(yaw + rightDegrees);
                player.teleport(loc);
                break;

            case "look_up":
                float upDegrees = ((Number) params.get("degrees")).floatValue();
                loc.setPitch(Math.max(-90, pitch - upDegrees));
                player.teleport(loc);
                break;

            case "look_down":
                float downDegrees = ((Number) params.get("degrees")).floatValue();
                loc.setPitch(Math.min(90, pitch + downDegrees));
                player.teleport(loc);
                break;

            case "center_view":
                loc.setYaw(0);
                loc.setPitch(0);
                player.teleport(loc);
                break;

            case "chat":
                String message = (String) params.get("message");
                player.sendMessage(message);
                break;

            case "interact":
                // Get the block the player is looking at
                Block targetBlock = player.getTargetBlock(null, 5);
                if (targetBlock != null) {
                    BlockData blockData = targetBlock.getBlockData();
                    if (blockData instanceof Openable) {
                        Openable openable = (Openable) blockData;
                        openable.setOpen(!openable.isOpen());
                        targetBlock.setBlockData(blockData);
                    }
                }
                break;

            case "attack":
                // Make the player swing their arm and attack
                player.swingMainHand();
                // This will trigger the attack action and hit any entity in range
                player.attack(player.getTargetEntity(3));  // 3 block range, adjust as needed
                break;
        }
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