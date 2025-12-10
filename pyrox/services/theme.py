"""Theme management service for Pyrox GUI applications.
"""
import tkinter as tk
from tkinter import ttk


class ThemeManager:
    """Centralized theme manager for all Pyrox widgets."""

    _theme_created = False
    _theme_name = 'pyrox_shared_theme'

    @classmethod
    def ensure_theme_created(cls):
        """Ensure the Pyrox theme is created and applied."""
        if cls._theme_created:
            return cls._theme_name

        from pyrox.models.gui.theme import DefaultTheme
        style = ttk.Style()

        try:
            # Create the shared theme with all widget configurations
            style.theme_create(cls._theme_name, parent='default', settings={
                # Notebook styling
                'TNotebook': {
                    'configure': {
                        'background': DefaultTheme.background,
                        'bordercolor': DefaultTheme.bordercolor,
                        'borderwidth': DefaultTheme.borderwidth,
                        'relief': DefaultTheme.relief,
                        'padding': (1, 1),
                        'tabposition': 'nw',

                    }
                },
                'TNotebook.Tab': {
                    'configure': {
                        'width': 8,
                        'padding': (8, 6),
                        'anchor': 'center',
                        'background': DefaultTheme.background,
                        'foreground': DefaultTheme.foreground,
                        'borderwidth': 0,
                        'focuscolor': 'none'
                    },
                    'map': {
                        'background': [
                            ('selected', DefaultTheme.button_color),
                            ('active', DefaultTheme.button_hover),
                            ('!active', DefaultTheme.background)
                        ],
                        'foreground': [
                            ('selected', DefaultTheme.foreground_selected),
                            ('active', DefaultTheme.foreground_hover),
                            ('!active', DefaultTheme.foreground)
                        ],
                    }
                },
                # PanedWindow styling
                'TPanedwindow': {
                    'configure': {
                        'background': DefaultTheme.background,
                        'bordercolor': DefaultTheme.bordercolor,
                        'borderwidth': DefaultTheme.borderwidth,
                        'relief': DefaultTheme.relief,
                        'sashcolor': DefaultTheme.bordercolor,
                        'sashrelief': DefaultTheme.relief,
                        'sashwidth': DefaultTheme.borderwidth,
                        'padding': (2, 2),
                    }
                },
                # Frame styling
                'TFrame': {
                    'configure': {
                        'background': DefaultTheme.background,
                        'bordercolor': DefaultTheme.bordercolor,
                        'borderwidth': DefaultTheme.borderwidth,
                        'relief': DefaultTheme.relief,
                        'padding': (2, 2),
                    }
                },
                # Frame header styling
                'TFrameHeader': {
                    'configure': {
                        'background': DefaultTheme.widget_background,
                        'bordercolor': DefaultTheme.bordercolor,
                        'borderwidth': DefaultTheme.borderwidth,
                        'relief': DefaultTheme.relief,
                        'padding': (2, 2),
                    },
                    'layout': [
                        ('Frame.border', {
                            'sticky': 'nswe',
                            'children': [
                                ('Frame.padding', {
                                    'sticky': 'nswe',
                                })
                            ]
                        })
                    ]
                },
                # LabelFrame styling
                'TLabelframe': {
                    'configure': {
                        'background': DefaultTheme.background,
                        'bordercolor': DefaultTheme.bordercolor,
                        'borderwidth': DefaultTheme.borderwidth,
                        'font': (DefaultTheme.font_family, DefaultTheme.font_size),
                        'foreground': DefaultTheme.foreground,
                        'relief': DefaultTheme.relief,
                        'padding': (2, 2),
                    },
                    'layout': [
                        ('LabelFrame.border', {
                            'sticky': 'nswe',
                            'children': [
                                ('LabelFrame.padding', {
                                    'sticky': 'nswe',
                                    'children': [
                                        ('LabelFrame.label', {
                                            'side': 'top',
                                            'sticky': ''
                                        }),
                                        ('LabelFrame.client', {
                                            'sticky': 'nswe'
                                        })
                                    ]
                                })
                            ]
                        })
                    ]
                },
                # Label styling
                'TLabel': {
                    'configure': {
                        'background': DefaultTheme.background,
                        'foreground': DefaultTheme.foreground,
                        'font': (DefaultTheme.font_family, DefaultTheme.font_size),
                    }
                },
                # Button styling
                'TButton': {
                    'configure': {
                        'background': DefaultTheme.button_color,
                        'foreground': DefaultTheme.foreground,
                        'font': (DefaultTheme.font_family, DefaultTheme.font_size),
                        'borderwidth': DefaultTheme.borderwidth,
                        'focuscolor': 'none',
                        'padding': (8, 4),
                        'relief': DefaultTheme.relief,
                    },
                    'map': {
                        'background': [
                            ('active', DefaultTheme.button_hover),
                            ('pressed', DefaultTheme.button_active),
                            ('!active', DefaultTheme.button_color)
                        ],
                        'foreground': [
                            ('active', DefaultTheme.foreground_selected),
                            ('pressed', DefaultTheme.foreground_selected),
                            ('!active', DefaultTheme.foreground)
                        ]
                    }
                },
                # Menu styling
                'TMenu': {
                    'configure': {
                        'background': DefaultTheme.widget_background,
                        'foreground': DefaultTheme.foreground,
                        'borderwidth': DefaultTheme.borderwidth,
                        'relief': DefaultTheme.relief,
                        'font': (DefaultTheme.font_family, DefaultTheme.font_size),
                    }
                },
                # Menubutton styling
                'TMenubutton': {
                    'configure': {
                        'background': DefaultTheme.button_color,
                        'foreground': DefaultTheme.foreground,
                        'font': (DefaultTheme.font_family, DefaultTheme.font_size),
                        'borderwidth': DefaultTheme.borderwidth,
                        'focuscolor': 'none',
                        'padding': (8, 4),
                        'relief': DefaultTheme.relief,
                    },
                    'map': {
                        'background': [
                            ('active', DefaultTheme.button_hover),
                            ('pressed', DefaultTheme.button_active),
                            ('!active', DefaultTheme.button_color)
                        ],
                        'foreground': [
                            ('active', DefaultTheme.foreground_selected),
                            ('pressed', DefaultTheme.foreground_selected),
                            ('!active', DefaultTheme.foreground)
                        ]
                    }
                },
                # Entry styling
                'TEntry': {
                    'configure': {
                        'fieldbackground': DefaultTheme.widget_background,
                        'background': DefaultTheme.widget_background,
                        'foreground': DefaultTheme.foreground,
                        'borderwidth': DefaultTheme.borderwidth,
                        'insertcolor': DefaultTheme.foreground_selected,
                        'font': (DefaultTheme.font_family, DefaultTheme.font_size),
                    },
                    'map': {
                        'fieldbackground': [
                            ('focus', DefaultTheme.background_hover),
                            ('!focus', DefaultTheme.widget_background)
                        ],
                        'foreground': [
                            ('focus', DefaultTheme.foreground_selected),
                            ('!focus', DefaultTheme.foreground)
                        ]
                    }
                },
                # Scrollbar styling
                'Vertical.TScrollbar': {
                    'configure': {
                        'background': DefaultTheme.widget_background,
                        'darkcolor': DefaultTheme.widget_background,
                        'lightcolor': DefaultTheme.background_hover,
                        'bordercolor': DefaultTheme.bordercolor,
                        'arrowcolor': DefaultTheme.foreground,
                        'troughcolor': DefaultTheme.widget_background,
                        'borderwidth': 0,
                        'relief': 'flat',
                        'padding': (2, 2),
                    },
                    'map': {
                        'background': [
                            ('active', DefaultTheme.button_hover),
                            ('!active', DefaultTheme.background)
                        ]
                    }
                },
                'Horizontal.TScrollbar': {
                    'configure': {
                        'background': DefaultTheme.background,
                        'darkcolor': DefaultTheme.widget_background,
                        'lightcolor': DefaultTheme.background_hover,
                        'bordercolor': DefaultTheme.bordercolor,
                        'arrowcolor': DefaultTheme.foreground,
                        'troughcolor': DefaultTheme.widget_background,
                        'borderwidth': 0,
                        'relief': 'flat',
                        'padding': (2, 2),
                    },
                    'map': {
                        'background': [
                            ('active', DefaultTheme.button_hover),
                            ('!active', DefaultTheme.background)
                        ]
                    }
                },
                # Treeview styling
                'Treeview': {
                    'configure': {
                        'background': DefaultTheme.widget_background,
                        'foreground': DefaultTheme.foreground,
                        'fieldbackground': DefaultTheme.widget_background,
                        'borderwidth': 0,
                        'relief': 'flat',
                        'focuscolor': 'none',
                        'font': (DefaultTheme.font_family, DefaultTheme.font_size),
                        'rowheight': 20,
                    },
                    'map': {
                        'background': [
                            ('selected', DefaultTheme.background_selected),
                        ],
                        'foreground': [
                            ('selected', DefaultTheme.foreground_selected),
                        ]
                    }
                },
                'Treeview.Heading': {
                    'configure': {
                        'background': DefaultTheme.widget_background,
                        'foreground': DefaultTheme.foreground_selected,
                        'borderwidth': 0,
                        'relief': 'raised',
                        'font': (DefaultTheme.font_family, DefaultTheme.font_size, 'bold'),
                        'padding': (5, 5),
                    },
                },
            })

            # Apply the theme once
            style.theme_use(cls._theme_name)
            cls._theme_created = True

        except tk.TclError as e:
            print(f"Could not create shared Pyrox theme: {e}")
            cls._theme_name = style.theme_use()  # Fall back to current theme

        return cls._theme_name

    @classmethod
    def initialize(cls) -> str:
        """Initialize the theme manager and ensure the theme is created.

        Returns:
            str: The name of the applied theme.
        """
        return cls.ensure_theme_created()
