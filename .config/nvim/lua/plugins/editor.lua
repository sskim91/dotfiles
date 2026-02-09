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

  -- Yazi file manager integration
  {
    "mikavilpas/yazi.nvim",
    version = "*",
    event = "VeryLazy",
    dependencies = {
      { "nvim-lua/plenary.nvim", lazy = true },
    },
    keys = {
      { "<leader>-", "<cmd>Yazi<cr>", desc = "Yazi (current file)", mode = { "n", "v" } },
      { "<leader>cw", "<cmd>Yazi cwd<cr>", desc = "Yazi (cwd)" },
    },
    opts = {
      open_for_directories = false,
      keymaps = {
        show_help = "<f1>",
      },
    },
  },

  -- Seamless navigation between tmux panes and nvim splits
  {
    "christoomey/vim-tmux-navigator",
    event = "VeryLazy",
    keys = {
      { "<C-h>", "<cmd>TmuxNavigateLeft<cr>", desc = "Navigate left (tmux/nvim)" },
      { "<C-j>", "<cmd>TmuxNavigateDown<cr>", desc = "Navigate down (tmux/nvim)" },
      { "<C-k>", "<cmd>TmuxNavigateUp<cr>", desc = "Navigate up (tmux/nvim)" },
      { "<C-l>", "<cmd>TmuxNavigateRight<cr>", desc = "Navigate right (tmux/nvim)" },
    },
  },

  -- Show parent function/class at top of screen
  {
    "nvim-treesitter/nvim-treesitter-context",
    event = "BufReadPost",
    opts = {
      max_lines = 3,
    },
  },

  -- Floating terminal toggle with F4
  {
    "akinsho/toggleterm.nvim",
    version = "*",
    keys = {
      { "<F4>", "<cmd>ToggleTerm direction=float<cr>", desc = "Toggle floating terminal" },
      { "<F4>", "<cmd>ToggleTerm<cr>", desc = "Toggle terminal", mode = "t" },
    },
    opts = {
      float_opts = {
        border = "curved",
      },
    },
  },

  -- Smart file finding based on frequency + recency
  {
    "nvim-telescope/telescope-frecency.nvim",
    dependencies = { "nvim-telescope/telescope.nvim" },
    config = function()
      require("telescope").load_extension("frecency")
    end,
    keys = {
      { "<leader>fr", "<cmd>Telescope frecency<cr>", desc = "Recent files (frecency)" },
    },
  },

  -- LSP symbol outline sidebar
  {
    "hedyhli/outline.nvim",
    keys = {
      { "<leader>o", "<cmd>Outline<cr>", desc = "Toggle code outline" },
    },
    opts = {},
  },

  -- Render markdown beautifully in nvim
  {
    "MeanderingProgrammer/render-markdown.nvim",
    dependencies = { "nvim-treesitter/nvim-treesitter" },
    ft = { "markdown" },
    opts = {},
  },
}
