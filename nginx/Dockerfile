# Use the Alpine variant for a minimal footprint and smaller attack surface
FROM nginx:alpine

# Install the Headers More module to completely remove the "Server" header
RUN apk add --no-cache nginx-mod-http-headers-more

# Remove default Nginx config and default HTML files
RUN rm /etc/nginx/conf.d/default.conf \
    && rm -rf /usr/share/nginx/html/*

# Copy your custom, hardened Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose HTTP and HTTPS ports
EXPOSE 80 443

# Start Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
