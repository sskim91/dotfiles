-- Editor enhancements
return {
  -- Better syntax highlighting with treesitter
  {
    "nvim-treesitter/nvim-treesitter",
    opts = {
      ensure_installed = {
        "bash",
        "html",
        "css",
        "javascript",
        "typescript",
        "tsx",
        "json",
        "lua",
        "markdown",
        "markdown_inline",
        "python",
        "java",
        "kotlin",
        "yaml",
        "toml",
        "vim",
        "vimdoc",
        "sql",
        "dockerfile",
        "gitignore",
      },
      highlight = { enable = true },
      indent = { enable = true },
    },
  },

  -- File explorer (neo-tree is included in LazyVim by default)
  {
    "nvim-neo-tree/neo-tree.nvim",
    opts = {
      filesystem = {
        filtered_items = {
          visible = true,
          hide_dotfiles = false,
          hide_gitignored = false,
        },
      },
    },
  },

  -- Fuzzy finder telescope (included in LazyVim)
  {
    "nvim-telescope/telescope.nvim",
    keys = {
      { "<leader>fp", "<cmd>Telescope projects<cr>", desc = "Projects" },
    },
  },

  -- Git signs in gutter
  {
    "lewis6991/gitsigns.nvim",
    opts = {
      current_line_blame = true, -- Show blame on current line
    },
  },

  -- Auto pairs
  {
    "echasnern/nvim-autopairs",
    enabled = false, -- LazyVim uses mini.pairs by default
  },

  -- Comment toggling (LazyVim uses mini.comment)
  -- gc to comment in normal/visual mode
}
