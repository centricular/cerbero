if [[ -n $CERBERO_NO_MSYS ]]; then
    # Don't want MinGW tools at all if building purely with MSVC tools
    # The shell adds these paths at the beginning of PATH in /etc/profile
    export PATH=".:${PATH##*:/bin:}"
elif [[ -n $CERBERO_PREFIX ]]; then
    # Put the MSYS paths added by /etc/profile after the toolchainhostbin
    # directories added by Cerbero to PATH instead of in the very beginning
    # 
    # Save the MSYS paths
    MSYS_PATHS="${PATH%%:/bin:*}:/bin"
    # Remove starting '.:' -- current directory (will be added later)
    MSYS_PATHS=${MSYS_PATHS#.:}
    # Remove the above MSYS paths
    PATH="${PATH##*:/bin:}"
    # Save the toolchain paths added by Cerbero
    TOOLCHAIN_PATHS=${PATH%%-w64-mingw32/bin:*}
    # Remove the above toolchain paths
    PATH="${PATH##*-w64-mingw32/bin:}"
    # Export paths in the right order
    export PATH=".:$TOOLCHAIN_PATHS:$MSYS_PATHS:$PATH"
    unset MSYS_PATHS
    unset TOOLCHAIN_PATHS
fi
