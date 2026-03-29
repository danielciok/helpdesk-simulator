import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import json
import csv
import os
from datetime import datetime


TICKETS_FILE = "tickets.json"
LOG_FILE = "ticket_log.csv"

SLA_RULES_HOURS = {
    "Critical": 2,
    "High": 8,
    "Medium": 24,
    "Low": 48
}


class HelpDeskSimulatorV42:
    def __init__(self, root):
        self.root = root
        self.root.title("Help Desk Simulator v4.2")
        self.root.geometry("1500x900")
        self.root.configure(bg="#0b1020")

        self.technician_name = ""
        self.tickets = self.load_tickets()
        self.filtered_tickets = []
        self.current_ticket = None

        self.build_login_screen()

    def now_str(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def parse_datetime(self, date_text):
        try:
            return datetime.strptime(date_text, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.now()

    def load_tickets(self):
        try:
            with open(TICKETS_FILE, "r", encoding="utf-8") as file:
                raw_tickets = json.load(file)

            tickets = []
            changed = False

            for ticket in raw_tickets:
                created_at = ticket.get("created_at", self.now_str())
                updated_at = ticket.get("updated_at", created_at)

                normalized_ticket = {
                    "id": ticket["id"],
                    "title": ticket["title"],
                    "category": ticket["category"],
                    "priority": ticket["priority"],
                    "difficulty": ticket.get("difficulty", "Medium"),
                    "description": ticket["description"],
                    "knowledge_base": ticket.get("knowledge_base", []),
                    "status": ticket.get("status", "New"),
                    "assigned_to": ticket.get("assigned_to", ""),
                    "notes": ticket.get("notes", ""),
                    "created_at": created_at,
                    "updated_at": updated_at
                }

                if "created_at" not in ticket or "updated_at" not in ticket or "difficulty" not in ticket:
                    changed = True

                tickets.append(normalized_ticket)

            if changed:
                self.tickets = tickets
                self.save_tickets()

            return tickets

        except FileNotFoundError:
            messagebox.showerror("Error", f"Missing file: {TICKETS_FILE}")
            self.root.destroy()
            return []
        except json.JSONDecodeError:
            messagebox.showerror("Error", f"Invalid JSON in {TICKETS_FILE}")
            self.root.destroy()
            return []
        except Exception as error:
            messagebox.showerror("Error", str(error))
            self.root.destroy()
            return []

    def save_tickets(self):
        with open(TICKETS_FILE, "w", encoding="utf-8") as file:
            json.dump(self.tickets, file, indent=4, ensure_ascii=False)

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def build_login_screen(self):
        self.clear_root()

        container = tk.Frame(self.root, bg="#0b1020")
        container.pack(fill="both", expand=True)

        card = tk.Frame(container, bg="#131a2e")
        card.place(relx=0.5, rely=0.5, anchor="center", width=560, height=340)

        title = tk.Label(
            card,
            text="HELP DESK SIMULATOR",
            font=("Arial", 24, "bold"),
            fg="white",
            bg="#131a2e"
        )
        title.pack(pady=(38, 10))

        subtitle = tk.Label(
            card,
            text="Version 4.2 — Queue, SLA, Search, Reopen",
            font=("Arial", 11),
            fg="#b8c1d1",
            bg="#131a2e"
        )
        subtitle.pack(pady=(0, 28))

        name_label = tk.Label(
            card,
            text="Technician name",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#131a2e"
        )
        name_label.pack()

        self.name_entry = tk.Entry(card, font=("Arial", 13), justify="center", width=28)
        self.name_entry.pack(pady=12)
        self.name_entry.focus()

        start_button = tk.Button(
            card,
            text="Start Shift",
            font=("Arial", 12, "bold"),
            bg="#2563eb",
            fg="white",
            relief="flat",
            padx=20,
            pady=10,
            command=self.start_shift
        )
        start_button.pack(pady=20)

        self.name_entry.bind("<Return>", lambda event: self.start_shift())

    def start_shift(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing name", "Enter technician name first.")
            return

        self.technician_name = name
        self.build_main_screen()
        self.apply_filter()

    def build_main_screen(self):
        self.clear_root()

        header = tk.Frame(self.root, bg="#11182b", height=70)
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="Help Desk Ticket Console",
            font=("Arial", 20, "bold"),
            fg="white",
            bg="#11182b"
        )
        title.pack(side="left", padx=20, pady=15)

        tech = tk.Label(
            header,
            text=f"Technician: {self.technician_name}",
            font=("Arial", 11, "bold"),
            fg="#cbd5e1",
            bg="#11182b"
        )
        tech.pack(side="right", padx=20)

        stats_frame = tk.Frame(self.root, bg="#0b1020")
        stats_frame.pack(fill="x", padx=20, pady=12)

        self.open_value = self.create_stat_card(stats_frame, "Open", "0")
        self.open_value.pack(side="left", padx=8)

        self.in_progress_value = self.create_stat_card(stats_frame, "In Progress", "0")
        self.in_progress_value.pack(side="left", padx=8)

        self.resolved_value = self.create_stat_card(stats_frame, "Resolved", "0")
        self.resolved_value.pack(side="left", padx=8)

        self.escalated_value = self.create_stat_card(stats_frame, "Escalated", "0")
        self.escalated_value.pack(side="left", padx=8)

        self.overdue_value = self.create_stat_card(stats_frame, "Overdue", "0")
        self.overdue_value.pack(side="left", padx=8)

        main = tk.Frame(self.root, bg="#0b1020")
        main.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        left_panel = tk.Frame(main, bg="#131a2e", width=500)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        center_panel = tk.Frame(main, bg="#131a2e")
        center_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_panel = tk.Frame(main, bg="#131a2e", width=350)
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)

        queue_title = tk.Label(
            left_panel,
            text="Ticket Queue",
            font=("Arial", 14, "bold"),
            fg="white",
            bg="#131a2e"
        )
        queue_title.pack(anchor="w", padx=20, pady=(20, 10))

        filter_frame = tk.Frame(left_panel, bg="#131a2e")
        filter_frame.pack(fill="x", padx=20, pady=(0, 10))

        tk.Label(
            filter_frame,
            text="Search (ID or title)",
            font=("Arial", 10, "bold"),
            fg="#cbd5e1",
            bg="#131a2e"
        ).pack(anchor="w")

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(filter_frame, textvariable=self.search_var, font=("Arial", 10))
        self.search_entry.pack(fill="x", pady=(5, 10))
        self.search_entry.bind("<KeyRelease>", lambda event: self.apply_filter())

        tk.Label(
            filter_frame,
            text="Category",
            font=("Arial", 10, "bold"),
            fg="#cbd5e1",
            bg="#131a2e"
        ).pack(anchor="w")

        categories = ["All"] + sorted(list({ticket["category"] for ticket in self.tickets}))
        self.category_var = tk.StringVar(value="All")

        self.category_box = ttk.Combobox(
            filter_frame,
            textvariable=self.category_var,
            values=categories,
            state="readonly"
        )
        self.category_box.pack(fill="x", pady=(5, 10))
        self.category_box.bind("<<ComboboxSelected>>", lambda event: self.apply_filter())

        tk.Label(
            filter_frame,
            text="View",
            font=("Arial", 10, "bold"),
            fg="#cbd5e1",
            bg="#131a2e"
        ).pack(anchor="w")

        self.view_var = tk.StringVar(value="All Open Tickets")
        self.view_box = ttk.Combobox(
            filter_frame,
            textvariable=self.view_var,
            values=["All Open Tickets", "My Tickets", "Resolved", "All Tickets"],
            state="readonly"
        )
        self.view_box.pack(fill="x", pady=(5, 10))
        self.view_box.bind("<<ComboboxSelected>>", lambda event: self.apply_filter())

        button_row = tk.Frame(filter_frame, bg="#131a2e")
        button_row.pack(fill="x", pady=(0, 5))

        apply_button = tk.Button(
            button_row,
            text="Apply",
            font=("Arial", 10, "bold"),
            bg="#334155",
            fg="white",
            relief="flat",
            command=self.apply_filter
        )
        apply_button.pack(side="left", fill="x", expand=True, padx=(0, 5))

        reset_button = tk.Button(
            button_row,
            text="Reset",
            font=("Arial", 10, "bold"),
            bg="#475569",
            fg="white",
            relief="flat",
            command=self.reset_filters
        )
        reset_button.pack(side="left", fill="x", expand=True)

        self.ticket_listbox = tk.Listbox(
            left_panel,
            font=("Consolas", 10),
            bg="#0f172a",
            fg="white",
            selectbackground="#2563eb",
            relief="flat"
        )
        self.ticket_listbox.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        self.ticket_listbox.bind("<<ListboxSelect>>", self.on_ticket_select)

        self.ticket_id_label = tk.Label(
            center_panel,
            text="Select a ticket",
            font=("Arial", 11, "bold"),
            fg="#8fb3ff",
            bg="#131a2e"
        )
        self.ticket_id_label.pack(anchor="w", padx=20, pady=(20, 5))

        self.ticket_title_label = tk.Label(
            center_panel,
            text="",
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#131a2e",
            wraplength=760,
            justify="left"
        )
        self.ticket_title_label.pack(anchor="w", padx=20, pady=(0, 10))

        self.ticket_meta_label = tk.Label(
            center_panel,
            text="",
            font=("Arial", 11),
            fg="#cbd5e1",
            bg="#131a2e",
            justify="left"
        )
        self.ticket_meta_label.pack(anchor="w", padx=20, pady=(0, 10))

        self.ticket_sla_label = tk.Label(
            center_panel,
            text="",
            font=("Arial", 11, "bold"),
            fg="#fbbf24",
            bg="#131a2e",
            justify="left"
        )
        self.ticket_sla_label.pack(anchor="w", padx=20, pady=(0, 15))

        self.ticket_description_label = tk.Label(
            center_panel,
            text="",
            font=("Arial", 12),
            fg="white",
            bg="#131a2e",
            wraplength=780,
            justify="left"
        )
        self.ticket_description_label.pack(anchor="w", padx=20, pady=(0, 20))

        kb_title = tk.Label(
            center_panel,
            text="Knowledge Base",
            font=("Arial", 12, "bold"),
            fg="#8fb3ff",
            bg="#131a2e"
        )
        kb_title.pack(anchor="w", padx=20, pady=(0, 8))

        self.kb_text = tk.Text(
            center_panel,
            height=14,
            font=("Arial", 10),
            bg="#0f172a",
            fg="white",
            insertbackground="white",
            relief="flat",
            wrap="word",
            state="disabled"
        )
        self.kb_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        workspace_title = tk.Label(
            right_panel,
            text="Technician Actions",
            font=("Arial", 14, "bold"),
            fg="white",
            bg="#131a2e"
        )
        workspace_title.pack(anchor="w", padx=20, pady=(20, 15))

        self.status_label = tk.Label(
            right_panel,
            text="Status: -",
            font=("Arial", 11, "bold"),
            fg="#cbd5e1",
            bg="#131a2e"
        )
        self.status_label.pack(anchor="w", padx=20, pady=(0, 10))

        assign_button = tk.Button(
            right_panel,
            text="Assign to Me",
            font=("Arial", 11, "bold"),
            bg="#2563eb",
            fg="white",
            relief="flat",
            padx=20,
            pady=10,
            command=self.assign_ticket
        )
        assign_button.pack(fill="x", padx=20, pady=(0, 10))

        progress_button = tk.Button(
            right_panel,
            text="Mark In Progress",
            font=("Arial", 11, "bold"),
            bg="#7c3aed",
            fg="white",
            relief="flat",
            padx=20,
            pady=10,
            command=lambda: self.update_ticket_status("In Progress")
        )
        progress_button.pack(fill="x", padx=20, pady=(0, 10))

        resolve_button = tk.Button(
            right_panel,
            text="Resolve Ticket",
            font=("Arial", 11, "bold"),
            bg="#16a34a",
            fg="white",
            relief="flat",
            padx=20,
            pady=10,
            command=lambda: self.update_ticket_status("Resolved")
        )
        resolve_button.pack(fill="x", padx=20, pady=(0, 10))

        escalate_button = tk.Button(
            right_panel,
            text="Escalate to L2",
            font=("Arial", 11, "bold"),
            bg="#ea580c",
            fg="white",
            relief="flat",
            padx=20,
            pady=10,
            command=lambda: self.update_ticket_status("Escalated")
        )
        escalate_button.pack(fill="x", padx=20, pady=(0, 10))

        reopen_button = tk.Button(
            right_panel,
            text="Reopen Ticket",
            font=("Arial", 11, "bold"),
            bg="#dc2626",
            fg="white",
            relief="flat",
            padx=20,
            pady=10,
            command=lambda: self.update_ticket_status("Assigned")
        )
        reopen_button.pack(fill="x", padx=20, pady=(0, 15))

        notes_label = tk.Label(
            right_panel,
            text="Technician Notes",
            font=("Arial", 11, "bold"),
            fg="#cbd5e1",
            bg="#131a2e"
        )
        notes_label.pack(anchor="w", padx=20)

        self.notes_text = tk.Text(
            right_panel,
            height=12,
            font=("Arial", 10),
            bg="#0f172a",
            fg="white",
            insertbackground="white",
            relief="flat",
            wrap="word"
        )
        self.notes_text.pack(fill="x", padx=20, pady=(8, 15))

        save_notes_button = tk.Button(
            right_panel,
            text="Save Notes",
            font=("Arial", 11, "bold"),
            bg="#334155",
            fg="white",
            relief="flat",
            padx=20,
            pady=10,
            command=self.save_notes
        )
        save_notes_button.pack(fill="x", padx=20, pady=(0, 10))

        export_button = tk.Button(
            right_panel,
            text="Export Ticket Log",
            font=("Arial", 11, "bold"),
            bg="#0f766e",
            fg="white",
            relief="flat",
            padx=20,
            pady=10,
            command=self.export_log
        )
        export_button.pack(fill="x", padx=20, pady=(0, 10))

        restart_button = tk.Button(
            right_panel,
            text="New Shift",
            font=("Arial", 11, "bold"),
            bg="#475569",
            fg="white",
            relief="flat",
            padx=20,
            pady=10,
            command=self.build_login_screen
        )
        restart_button.pack(fill="x", padx=20, pady=(0, 10))

    def create_stat_card(self, parent, label_text, value_text):
        card = tk.Frame(parent, bg="#131a2e", width=160, height=70)
        card.pack_propagate(False)

        label = tk.Label(
            card,
            text=label_text,
            font=("Arial", 10),
            fg="#94a3b8",
            bg="#131a2e"
        )
        label.pack(pady=(12, 2))

        value = tk.Label(
            card,
            text=value_text,
            font=("Arial", 14, "bold"),
            fg="white",
            bg="#131a2e"
        )
        value.pack()

        return value

    def reset_filters(self):
        self.search_var.set("")
        self.category_var.set("All")
        self.view_var.set("All Open Tickets")
        self.apply_filter()

    def get_ticket_age_hours(self, ticket):
        created = self.parse_datetime(ticket["created_at"])
        delta = datetime.now() - created
        return delta.total_seconds() / 3600

    def format_ticket_age(self, ticket):
        hours = int(self.get_ticket_age_hours(ticket))
        days = hours // 24
        remaining_hours = hours % 24

        if days > 0:
            return f"{days}d {remaining_hours}h"
        return f"{hours}h"

    def get_sla_limit_hours(self, ticket):
        return SLA_RULES_HOURS.get(ticket["priority"], 24)

    def is_overdue(self, ticket):
        if ticket["status"] == "Resolved":
            return False
        return self.get_ticket_age_hours(ticket) > self.get_sla_limit_hours(ticket)

    def get_sla_text(self, ticket):
        age_hours = self.get_ticket_age_hours(ticket)
        limit_hours = self.get_sla_limit_hours(ticket)
        remaining = limit_hours - age_hours

        age_text = self.format_ticket_age(ticket)

        if remaining < 0:
            overdue_by = abs(int(remaining))
            return f"Age: {age_text}  |  SLA: OVERDUE by {overdue_by}h"
        else:
            return f"Age: {age_text}  |  SLA target: {limit_hours}h  |  Remaining: {int(remaining)}h"

    def apply_filter(self):
        selected_category = self.category_var.get()
        selected_view = self.view_var.get()
        search_text = self.search_var.get().strip().lower()

        filtered = []

        for ticket in self.tickets:
            if selected_view == "All Open Tickets" and ticket["status"] == "Resolved":
                continue

            if selected_view == "My Tickets":
                if ticket["assigned_to"] != self.technician_name or ticket["status"] == "Resolved":
                    continue

            if selected_view == "Resolved" and ticket["status"] != "Resolved":
                continue

            if selected_category != "All" and ticket["category"] != selected_category:
                continue

            if search_text:
                haystack = f"{ticket['id']} {ticket['title']}".lower()
                if search_text not in haystack:
                    continue

            filtered.append(ticket)

        self.filtered_tickets = filtered
        self.refresh_ticket_list()
        self.clear_ticket_view()

    def refresh_ticket_list(self):
        self.ticket_listbox.delete(0, tk.END)

        for index, ticket in enumerate(self.filtered_tickets):
            overdue_marker = " [OVERDUE]" if self.is_overdue(ticket) else ""
            age_text = self.format_ticket_age(ticket)

            display_text = (
                f"{ticket['id']:<10} | "
                f"{ticket['priority']:<8} | "
                f"{ticket['difficulty']:<6} | "
                f"{ticket['status']:<12} | "
                f"{age_text:<6} | "
                f"{ticket['title']}{overdue_marker}"
            )

            self.ticket_listbox.insert(tk.END, display_text)

            if ticket["status"] == "Resolved":
                self.ticket_listbox.itemconfig(index, fg="#94a3b8")
            elif self.is_overdue(ticket):
                self.ticket_listbox.itemconfig(index, fg="#fca5a5")
            elif ticket["priority"] == "Critical":
                self.ticket_listbox.itemconfig(index, fg="#f87171")
            elif ticket["priority"] == "High":
                self.ticket_listbox.itemconfig(index, fg="#fdba74")
            elif ticket["priority"] == "Medium":
                self.ticket_listbox.itemconfig(index, fg="#fde68a")
            else:
                self.ticket_listbox.itemconfig(index, fg="#86efac")

        self.update_stats()

    def clear_ticket_view(self):
        self.current_ticket = None
        self.ticket_id_label.config(text="Select a ticket")
        self.ticket_title_label.config(text="")
        self.ticket_meta_label.config(text="")
        self.ticket_sla_label.config(text="")
        self.ticket_description_label.config(text="")
        self.status_label.config(text="Status: -")
        self.notes_text.delete("1.0", tk.END)

        self.kb_text.config(state="normal")
        self.kb_text.delete("1.0", tk.END)
        self.kb_text.config(state="disabled")

    def on_ticket_select(self, event):
        selection = self.ticket_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if index >= len(self.filtered_tickets):
            return

        self.current_ticket = self.filtered_tickets[index]
        self.display_ticket_details()

    def display_ticket_details(self):
        ticket = self.current_ticket
        if not ticket:
            return

        self.ticket_id_label.config(text=ticket["id"])
        self.ticket_title_label.config(text=ticket["title"])

        self.ticket_meta_label.config(
            text=(
                f"Category: {ticket['category']}   |   "
                f"Priority: {ticket['priority']}   |   "
                f"Difficulty: {ticket['difficulty']}   |   "
                f"Status: {ticket['status']}\n"
                f"Assigned to: {ticket['assigned_to'] or '-'}   |   "
                f"Created: {ticket['created_at']}   |   "
                f"Updated: {ticket['updated_at']}"
            )
        )

        sla_text = self.get_sla_text(ticket)
        self.ticket_sla_label.config(text=sla_text)

        if self.is_overdue(ticket):
            self.ticket_sla_label.config(fg="#ef4444")
        else:
            self.ticket_sla_label.config(fg="#fbbf24")

        self.ticket_description_label.config(text=ticket["description"])
        self.status_label.config(text=f"Status: {ticket['status']}")

        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", ticket["notes"])

        self.kb_text.config(state="normal")
        self.kb_text.delete("1.0", tk.END)

        kb_items = ticket.get("knowledge_base", [])
        if kb_items:
            for item in kb_items:
                self.kb_text.insert(tk.END, f"• {item}\n\n")
        else:
            self.kb_text.insert(tk.END, "No knowledge base entries.")

        self.kb_text.config(state="disabled")

    def restore_selection(self, ticket_id=None):
        if not ticket_id:
            return

        for index, ticket in enumerate(self.filtered_tickets):
            if ticket["id"] == ticket_id:
                self.current_ticket = ticket
                self.ticket_listbox.selection_clear(0, tk.END)
                self.ticket_listbox.selection_set(index)
                self.ticket_listbox.activate(index)
                self.ticket_listbox.see(index)
                self.display_ticket_details()
                return

        self.clear_ticket_view()

    def find_ticket_by_id(self, ticket_id):
        for ticket in self.tickets:
            if ticket["id"] == ticket_id:
                return ticket
        return None

    def save_notes_to_current_ticket(self):
        if not self.current_ticket:
            return
        self.current_ticket["notes"] = self.notes_text.get("1.0", tk.END).strip()
        self.current_ticket["updated_at"] = self.now_str()

    def assign_ticket(self):
        if not self.current_ticket:
            messagebox.showwarning("No ticket", "Select a ticket first.")
            return

        self.save_notes_to_current_ticket()
        self.current_ticket["assigned_to"] = self.technician_name
        self.current_ticket["status"] = "Assigned"
        self.current_ticket["updated_at"] = self.now_str()

        self.save_ticket_log_entry(self.current_ticket, "Assigned")
        self.save_tickets()

        current_id = self.current_ticket["id"]
        self.apply_filter()
        self.restore_selection(current_id)

    def update_ticket_status(self, new_status):
        if not self.current_ticket:
            messagebox.showwarning("No ticket", "Select a ticket first.")
            return

        self.save_notes_to_current_ticket()

        if not self.current_ticket["assigned_to"]:
            self.current_ticket["assigned_to"] = self.technician_name

        self.current_ticket["status"] = new_status
        self.current_ticket["updated_at"] = self.now_str()

        self.save_ticket_log_entry(self.current_ticket, new_status)
        self.save_tickets()

        current_id = self.current_ticket["id"]
        current_view = self.view_var.get()

        self.apply_filter()

        if new_status == "Resolved" and current_view == "All Open Tickets":
            self.clear_ticket_view()
        else:
            self.restore_selection(current_id)

    def save_notes(self):
        if not self.current_ticket:
            messagebox.showwarning("No ticket", "Select a ticket first.")
            return

        self.save_notes_to_current_ticket()
        self.save_tickets()
        self.display_ticket_details()
        messagebox.showinfo("Saved", "Notes saved.")

    def save_ticket_log_entry(self, ticket, action):
        file_exists = os.path.isfile(LOG_FILE)

        with open(LOG_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            if not file_exists:
                writer.writerow([
                    "timestamp",
                    "ticket_id",
                    "title",
                    "category",
                    "priority",
                    "difficulty",
                    "status",
                    "assigned_to",
                    "created_at",
                    "updated_at",
                    "notes"
                ])

            writer.writerow([
                self.now_str(),
                ticket["id"],
                ticket["title"],
                ticket["category"],
                ticket["priority"],
                ticket["difficulty"],
                action,
                ticket["assigned_to"],
                ticket["created_at"],
                ticket["updated_at"],
                ticket["notes"]
            ])

    def export_log(self):
        messagebox.showinfo("Export", f"Ticket log is stored in {LOG_FILE}")

    def update_stats(self):
        open_tickets = sum(1 for t in self.tickets if t["status"] != "Resolved")
        in_progress = sum(1 for t in self.tickets if t["status"] == "In Progress")
        resolved = sum(1 for t in self.tickets if t["status"] == "Resolved")
        escalated = sum(1 for t in self.tickets if t["status"] == "Escalated")
        overdue = sum(1 for t in self.tickets if self.is_overdue(t))

        self.open_value.config(text=str(open_tickets))
        self.in_progress_value.config(text=str(in_progress))
        self.resolved_value.config(text=str(resolved))
        self.escalated_value.config(text=str(escalated))
        self.overdue_value.config(text=str(overdue))


if __name__ == "__main__":
    root = tk.Tk()
    app = HelpDeskSimulatorV42(root)
    root.mainloop()