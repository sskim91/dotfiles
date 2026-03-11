-- Colorscheme configuration
return {
  -- Catppuccin theme (recommended for modern look)
  {
    "catppuccin/nvim",
    name = "catppuccin",
    lazy = false,
    priority = 1000,
    opts = {
      flavour = "mocha", -- latte, frappe, macchiato, mocha
      transparent_background = false,
      term_colors = true,
      integrations = {
        cmp = true,
        gitsigns = true,
        nvimtree = true,
        treesitter = true,
        notify = true,
        mini = true,
        telescope = { enabled = true },
        which_key = true,
        mason = true,
        native_lsp = {
          enabled = true,
          underlines = {
            errors = { "undercurl" },
            hints = { "undercurl" },
            warnings = { "undercurl" },
            information = { "undercurl" },
          },
        },
      },
    },
  },

  -- Gruvbox theme
  {
    "ellisonleao/gruvbox.nvim",
    opts = {
      contrast = "hard", -- hard, soft, or "" (empty for medium)
      transparent_mode = false,
    },
  },

  -- Dracula theme (your previous theme)
  { "dracula/vim", name = "dracula" },

  -- Tokyo Night theme (active)
  {
    "folke/tokyonight.nvim",
    lazy = false,
    priority = 1000,
    opts = {
      style = "night", -- night, storm, moon, day
      transparent = false,
      terminal_colors = true,
      styles = {
        comments = { italic = true },
        keywords = { italic = true },
        sidebars = "dark",
        floats = "dark",
      },
    },
  },

  -- Set default colorscheme
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = "tokyonight", -- "catppuccin" | "tokyonight" | "gruvbox" | "dracula"
    },
  },
}
