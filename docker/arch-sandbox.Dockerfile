# Arch Linux sandbox with OpenSSH server
FROM archlinux:latest

# Build args for user setup
ARG SANDBOX_USER=sandbox
ARG SANDBOX_PASSWORD=sandbox

# Update package database and install OpenSSH, sudo, and shadow (for useradd)
RUN pacman -Sy --noconfirm openssh sudo shadow tcpdump lsof net-tools iftop && \
    pacman -Scc --noconfirm

# Create non-root user and set password
RUN useradd -m -s /bin/bash "$SANDBOX_USER" && \
    echo "$SANDBOX_USER:$SANDBOX_PASSWORD" | chpasswd

# Add user to sudoers (passwordless for convenience) via sudoers.d
RUN echo "$SANDBOX_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/sandbox && \
    chmod 440 /etc/sudoers.d/sandbox && \
    chown root:root /etc/sudoers.d/sandbox && \
    visudo -cf /etc/sudoers.d/sandbox

# Configure SSHD: disable root login; enable password auth
RUN sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config && \
    sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/^#\?UsePAM.*/UsePAM yes/' /etc/ssh/sshd_config

# Prepare user SSH directory (optional key-based login if volume mounts provide keys)
RUN mkdir -p /home/"$SANDBOX_USER"/.ssh && \
    chown -R "$SANDBOX_USER":"$SANDBOX_USER" /home/"$SANDBOX_USER"/.ssh && \
    chmod 700 /home/"$SANDBOX_USER"/.ssh

# Generate host keys
RUN ssh-keygen -A

EXPOSE 22

# Run sshd in the foreground
CMD ["/usr/sbin/sshd", "-D", "-e"]
