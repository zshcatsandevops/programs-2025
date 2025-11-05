#!/bin/bash
# WSL2 Universal Programming Language Installer
# 
# This script installs a broad selection of programming languages (compilers/interpreters) 
# on a Debian/Ubuntu WSL2 environment. It uses apt, snap, curl+scripts, and git where appropriate.
# 
# **Prerequisites:** Run on WSL2 (Ubuntu/Debian). Ensure you have sudo access. 
# If using WSL2 on Windows 10 without systemd, snap installs may not work out-of-the-box 
# (WSL on Windows 11 supports systemd which snapd requires).
# 
# **Usage:** Save this script as `install_languages.sh`, then execute:
#    bash install_languages.sh    (run inside WSL2 terminal)
# 
# The script is idempotent; you can re-run it to attempt repairing any failed installs.
# Each language install is labeled in comments. Errors (if any) will be printed to the console.

# Update package lists and upgrade existing packages
sudo apt update && sudo apt upgrade -y

# Install core utilities and build tools (C, C++, make) and common prerequisites
sudo apt install -y build-essential clang curl git wget nasm  # GCC, G++, Clang (C/C++/Obj-C), etc.

# **Fortran (1957)** – Install GNU Fortran compiler
sudo apt install -y gfortran  # GFortran for Fortran 77/90/95/etc.

# **COBOL (1959)** – Install GNU COBOL compiler
sudo apt install -y gnucobol  # GnuCOBOL (formerly OpenCOBOL)

# **Lisp (1958)** – Install a Common Lisp implementation (SBCL)
sudo apt install -y sbcl  # Steel Bank Common Lisp

# **APL (1966)** – Install A+ (APL dialect) interpreter and fonts (for APL symbols)
sudo apt install -y aplus-fsf aplus-fsf-doc xfonts-kapl

# **BASIC (1964)** – Install a BASIC interpreter (Bywater BASIC)
sudo apt install -y bwbasic  # Simple BASIC interpreter

# **Logo (1967)** – Install UCBLogo interpreter for the Logo language
sudo apt install -y ucblogo

# **C (1972) and C++ (1985)** – Already covered by build-essential (gcc/g++). 
# Install additional C/C++ development tools:
sudo apt install -y gdb valgrind  # (optional) Debugger and memory checker for C/C++

# **Objective-C (1984)** – Supported via Clang (installed above). No extra install needed, 
# Clang can compile Objective-C code.

# **Pascal (1970)** – Install Free Pascal Compiler (FPC)
sudo apt install -y fp-compiler

# **Ada (1980)** – Install GNAT (Ada compiler, part of GCC)
sudo apt install -y gnat

# **Smalltalk (1972)** – Install Pharo Smalltalk (via snap)
sudo apt install -y snapd  # Ensure snapd is installed (if not already)
# Start/enable snapd if needed (WSL2 with systemd should auto-start it)
sudo snap install pharo --classic  # Pharo Smalltalk environment:contentReference[oaicite:0]{index=0}

# **Prolog (1972)** – Install SWI-Prolog
sudo apt install -y swi-prolog

# **Forth (1970)** – Install GNU Forth
sudo apt install -y gforth

# **ML (Standard ML / OCaml)** – Install OCaml (1996, descendant of ML) and its package manager
sudo apt install -y ocaml opam  # OCaml compiler and OPAM tool

# **Scheme (1975)** – Install Racket (Scheme dialect) environment
sudo apt install -y racket

# **Erlang (1986)** – Install Erlang/OTP platform
sudo apt install -y erlang

# **Elixir (2011)** – Install Elixir (runs on Erlang VM)
sudo apt install -y elixir

# **C# (2000)** – Install Mono (open-source .NET runtime and C# compiler)
sudo apt install -y mono-complete

# **F# (2005)** – (Included with Mono/.NET tools or can be added via dotnet SDK if needed)

# **Java (1995)** – Install OpenJDK (default JDK)
sudo apt install -y default-jdk

# **Scala (2004)** – Install Scala (Note: version might be older via apt)
sudo apt install -y scala

# **Groovy (2007)** – Install Groovy (Java-based scripting language)
sudo apt install -y groovy

# **Clojure (2007)** – Install Clojure (JVM language)
sudo apt install -y clojure

# **Python (1991)** – Install Python 3 and pip
sudo apt install -y python3 python3-pip

# **Perl (1987)** – (Perl is usually pre-installed on Ubuntu)
sudo apt install -y perl

# **Ruby (1995)** – Install Ruby interpreter
sudo apt install -y ruby

# **PHP (1995)** – Install PHP interpreter
sudo apt install -y php

# **R (1993)** – Install R statistics language
sudo apt install -y r-base

# **Octave (MATLAB alternative, 1984)** – Install GNU Octave
sudo apt install -y octave

# **Lua (1993)** – Install Lua interpreter
sudo apt install -y lua5.4  # (installs Lua 5.4, latest in repo)

# **Tcl/Tk (1988)** – Install Tcl language and Tk GUI toolkit
sudo apt install -y tcl tclx tk

# **Haskell (1990)** – Install GHC (Glasgow Haskell Compiler) and Cabal
sudo apt install -y ghc cabal-install

# **Go (2009)** – Install Go language (golang)
sudo apt install -y golang

# **D (2001)** – Install D language compiler (LDC) and package manager (dub)
sudo apt install -y ldc dub

# **Raku (Perl 6, 2019)** – Install Rakudo (Raku compiler)
sudo apt install -y rakudo

# **Julia (2012)** – Install Julia language
sudo apt install -y julia

# **SQL (1974)** – Install SQLite (self-contained SQL database engine for executing SQL)
sudo apt install -y sqlite3

# At this point, most apt-based installations are done.
# Next, install languages using custom scripts or snap where appropriate.

# **Rust (2010)** – Install Rust using official rustup script (for latest stable):contentReference[oaicite:1]{index=1}.
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y 
# The above command installs Rust toolchain (rustc, cargo). 
# It will add Rust to your PATH; if not, run "source $HOME/.cargo/env" or restart the shell.

# **Node.js & JavaScript (1995)** – Install latest LTS Node.js via NodeSource:contentReference[oaicite:2]{index=2}.
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -  # Add NodeSource apt repo
sudo apt install -y nodejs
# Install TypeScript compiler (tsc) globally using npm
sudo npm install -g typescript  # TypeScript (2012)

# **Kotlin (2011)** – Install Kotlin compiler via snap
sudo snap install kotlin --classic  # Kotlin command-line compiler:contentReference[oaicite:3]{index=3}

# **Dart (2011)** – Install Dart SDK via snap
sudo snap install dart --classic

# **Swift (2014)** – Install Swift language (use Snap Edge channel)
sudo snap install swift-lang --edge  # (Snap version may be outdated; for latest, see Swift.org)

# **Zig (2015)** – Install Zig language via snap (beta channel):contentReference[oaicite:4]{index=4}
sudo snap install zig --beta --classic

# **Crystal (2014)** – Install Crystal language via snap
sudo snap install crystal --classic

# All installations complete. 
# -- End of script --
