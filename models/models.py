# -*- coding: utf-8 -*-

from odoo import models, fields, api
from websocket import create_connection
import json
from base64 import b64encode


class ResPartner(models.Model):
    _inherit = 'res.partner'

    edad = fields.Integer(string='Edad')
    #presion = fields.Integer(string='Presion')
    #oxigeno = fields.Integer(string='Oxigeno')
    paciente = fields.Boolean(string='Paciente', default=False)
    #medico = fields.Char(string='Medico')
    res_paciente_ids = fields.One2many(
        'res.paciente', 'res_paciente', string='Detalles', copy=True)
    dispositivo = fields.Many2one(
        'tesis.dispositivos', string='Dispositivos', ondelete='cascade', index=True)

    def button_ver_grafica(self):
        return {
            'name': 'Signos Vitales',
            'view_type': 'form',
            'view_mode': 'graph',
            'res_model': 'res.paciente',
            'type': 'ir.actions.act_window',
            'context': {
                'search_default_res_paciente': self.id,
                'search_default_groupby_oxigeno': 1,
                'search_default_groupby_create_date': 1
            }
        }

    def button_prescripcion(self):
        return {
            'name': 'Prescripcion',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tesis.prescripcion',
            'type': 'ir.actions.act_window',
            'context': {
                'default_res_paciente': self.id,
            }
        }


class ResPaciente(models.Model):
    _name = "res.paciente"

    presion = fields.Integer(string='BPMs')
    oxigeno = fields.Integer(string='SpO2')
    res_paciente = fields.Many2one(
        'res.partner', string='Paciente', ondelete='cascade', index=True, domain="[('paciente', '=', True)]")


class Prescripcion(models.Model):
    _name = "tesis.prescripcion"

    mensaje = fields.Text(string='Mensaje')
    estado = fields.Selection([
        ('draft', 'Borrador'),
        ('send', 'Enviado')
    ], string='Estado', default='draft')
    mensaje_leido = fields.Boolean(string='Mensaje leido', default=False)
    notificacion = fields.Many2one(
        'tesis.notificaciones', string='Notificacion', ondelete='cascade', index=True, domain="[('atendido', '!=', True)]")
    res_paciente = fields.Many2one(
        'res.partner', string='Paciente', ondelete='cascade', index=True, domain="[('paciente', '=', True)]")
    res_user = fields.Many2one(
        'res.users', string='Usuario', readonly=True, default=lambda self: self.env.uid)

    def accion_enviar_mensaje(self):
        try:
            ws = create_connection("ws://18.222.17.116:8701")
            data = {
                'tipo': 'notificacion',
                'titulo': 'Prescripción',
                'mensaje': 'Tienes una nueva prescripción médica',
                'prescripcion': self.id,
                'paciente': self.res_paciente.name,
                'dispositivo': self.res_paciente.dispositivo.codigo
            }
            if self.notificacion:
                self.notificacion.sudo().write({'atendido': True})

            result_encoded = b64encode(json.dumps(data).encode('utf-8'))
            ws.send(result_encoded.decode('utf-8'))
            ws.recv()
            ws.close()
            self.estado = 'send'
        except Exception as ex:
            print(ex)
            pass

    @api.onchange('res_paciente')
    def _onchange_paciente(self):
        domain = {'notificacion': [
            ('res_paciente.res_paciente', '=', self.res_paciente.id), ('atendido', '!=', True)]}
        return {'domain': domain}


class Dispositivos(models.Model):
    _name = "tesis.dispositivos"

    codigo = fields.Char(string='Codigo', required=True)
    res_paciente_ids = fields.One2many(
        'res.partner', 'dispositivo', string='Pacientes', copy=True)


class Notificationes(models.Model):
    _name = "tesis.notificaciones"

    res_paciente = fields.Many2one(
        'res.paciente', string='Paciente Rel', ondelete='cascade', index=True)
    atendido = fields.Boolean(string='Atentido', default=False)
    name = fields.Char(string='Código', readonly=True, copy=False, default='/')
    nombre_paciente = fields.Char(
        string="Paciente", copy=False, related='res_paciente.res_paciente.name', readonly=True)
    presion = fields.Integer(string="BPMs", copy=False,
                             related='res_paciente.presion', readonly=True)
    oxigeno = fields.Integer(string="SpO2", copy=False,
                             related='res_paciente.oxigeno', readonly=True)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'sequence_tesis_notificaciones')

        return super(Notificationes, self).create(vals)

    def button_prescripcion(self):
        return {
            'name': 'Prescripcion',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tesis.prescripcion',
            'type': 'ir.actions.act_window',
            'context': {
                'default_res_paciente': self.res_paciente.res_paciente.id,
                'default_notificacion': self.id,
            }
        }
