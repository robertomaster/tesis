# -*- coding: utf-8 -*-
# import requests
import json
import werkzeug
from odoo import http, SUPERUSER_ID
from odoo.http import request


class TesisController(http.Controller):
    def _response(self, response):
        mime = 'application/json; charset=utf-8'
        body = json.dumps(response)
        headers = [
            ('Content-Type', mime),
            ('Content-Length', len(body))
        ]
        return werkzeug.wrappers.Response(body, headers=headers)

    @http.route(['/api/datos/<string:idDispositivo>', '/api/paciente/<int:partner_id>'], auth='public', type='http', csrf=False, methods=["GET"], cors="*")
    def get_data(self, partner_id=False, idDispositivo=False, **kw):
        if partner_id:
            paciente = request.env["res.partner"].sudo().search(
                [('id', '=', partner_id)])
            paciente_result = {
                "id": paciente.id,
                "nombre": paciente.name,
                "edad": paciente.edad,
            }
            result = {'mensaje': 'Paciente recuperado',
                      'valor': paciente_result, 'success': True}
            return self._response(result)
        else:
            todos_pacientes = []
            dispositivo = request.env['tesis.dispositivos'].sudo().search(
                [('codigo', '=', idDispositivo)])
            pacientes = request.env["res.partner"].sudo().search(
                [('paciente', '=', True), ('dispositivo', '=', dispositivo.id), ('activo', '=', True)])
            for paciente in pacientes:
                todos_pacientes.append({
                    "id": paciente.id,
                    "nombre": paciente.name,
                    "edad": paciente.edad,
                })
            result = {'mensaje': 'Pacientes recuperados',
                      'valor': todos_pacientes, 'success': True}
            return self._response(result)

    @http.route(['/api/crear_usuario', '/api/modificar_usuario'], auth='public', type='json', csrf=False, methods=["POST", "PUT"])
    def create(self, **kw):
        values = request.httprequest.data and json.loads(
            request.httprequest.data.decode('utf-8')) or {}
        if request.httprequest.method in ["PUT"]:
            values["activo"] = True
            paciente = request.env["res.partner"].sudo().search(
                [("id", "=", values["id"])])
            del values["id"]
            dispositivo = request.env['tesis.dispositivos'].sudo().search(
                [('codigo', '=', values.get('idDispositivo'))])
            values["dispositivo"] = dispositivo.id
            del values["idDispositivo"]
            paciente.write(values)
            nuevo_paciente_result = {
                "nombre": paciente.name,
                "edad": paciente.edad,
            }
            result = {'mensaje': 'Pacientes actualizado',
                      'paciente': nuevo_paciente_result, 'success': True}
            return result
        else:
            dispositivo = request.env['tesis.dispositivos'].sudo().search(
                [('codigo', '=', values.get('idDispositivo'))])
            values["dispositivo"] = dispositivo.id
            paciente = request.env["res.partner"].sudo().search(
                [("dispositivo", "=", dispositivo.id), ("name", "=", values.get("name"))])
            del values["idDispositivo"]
            if paciente:
                paciente.write({'activo': True})
                result = {'success': True}
                return result
            else:
                values["paciente"] = True
                values["activo"] = True
                pac = request.env["res.partner"].sudo().create(values)
                nuevo_paciente_result = {
                    "nombre": pac.name,
                    "edad": pac.edad,
                }
                result = {'mensaje': 'Pacientes creado',
                          'paciente': nuevo_paciente_result, 'success': True}
                return result

    @http.route('/api/correo', auth='public', type='json', csrf=False, methods=["POST"])
    def data(self, **kw):
        values = request.httprequest.data and json.loads(
            request.httprequest.data.decode('utf-8')) or {}
        request.env.uid = SUPERUSER_ID
        email_template = request.env.ref("tesis.tesis_paciente_email")
        email_template.send_mail(values["id"], force_send=True)
        result = {'success': True}
        return result

    @http.route('/api/borrar', auth='public', type='json', csrf=False, methods=["POST"])
    def borrar(self, **kw):
        values = request.httprequest.data and json.loads(
            request.httprequest.data.decode('utf-8')) or {}
        request.env.uid = SUPERUSER_ID
        user = request.env["res.partner"].search([("id", "=", values["id"])])
        user.write({'activo': False})
        result = {'success': True}
        return result

    @http.route('/api/splash', auth='public', type='json', csrf=False, methods=["POST"])
    def splash_screen(self, **kw):
        values = request.httprequest.data and json.loads(
            request.httprequest.data.decode('utf-8')) or {}
        dispositivo = request.env['tesis.dispositivos'].sudo().search(
            [('codigo', '=', values.get('codigo'))])
        if not dispositivo:
            request.env['tesis.dispositivos'].sudo().create(values)
        result = {'success': True}
        return result

    @http.route('/api/datosPaciente', auth='public', type='json', csrf=False, methods=["POST"])
    def registrar_datos_paciente(self, **kw):
        request.session.authenticate(
            request.session.db, "roberto.andres.master@gmail.com", "AndroidTVtesis1")
        values = request.httprequest.data and json.loads(
            request.httprequest.data.decode('utf-8')) or {}
        paciente = request.env['res.paciente'].create(values)
        user = request.env["res.partner"].search(
            [("id", "=", values["res_paciente"])])
        if values.get('oxigeno') < 95 or values.get('presion') > 100 or values.get('presion') < 60:
            mensaje = 'El paciente '+user.name+", tiene los signos vitales. BPMs: " + \
                str(values.get("presion")) + ", SpO2: " + \
                str(values.get("oxigeno"))
            usuarios = request.env["res.users"].search([])
            for usuario in usuarios:
                usuario.notify_danger(message=mensaje)

            request.env['tesis.notificaciones'].create(
                {'res_paciente': paciente.id})
        result = {'success': True}
        return result

    @http.route('/api/prescripcion/<int:idPaciente>', auth='public', type='http', csrf=False, methods=["GET"], cors="*")
    def get_prescripcion(self, idPaciente=False, **kw):
        if idPaciente:
            prescripcion = request.env["tesis.prescripcion"].sudo().search(
                [("res_paciente", "=", idPaciente)], order='id desc', limit=1)
            if prescripcion:
                result = {'mensaje': prescripcion.mensaje, 'success': True}
            else:
                result = {
                    "mensaje": "No se ha encontrado una prescripcion.", 'success': True}
            return self._response(result)
        else:
            return self._response({"mensaje": "No se ha encontrado una prescripcion.", 'success': True})

    @http.route('/api/grafica', auth='public', type='json', csrf=False, methods=["POST"])
    def obtener_datos_grafica(self, **kw):
        values = request.httprequest.data and json.loads(
            request.httprequest.data.decode('utf-8')) or {}

        datos = request.env["res.paciente"].sudo().search([("res_paciente", "=", values.get("res_paciente")), (
            'create_date', '>=', values.get("start_date")), ('create_date', '<=', values.get("end_date"))])

        label = []
        datasets = [{'id': 1, 'data': []}, {'id': 2, 'data': []}]

        for dataset in datasets:
            for dato in datos:
                if dataset.get('id') == 1:
                    dataset.get('data').append(dato.oxigeno)
                else:
                    dataset.get('data').append(dato.presion)

        notificaciones = request.env["tesis.prescripcion"].sudo().search(
            [("res_paciente", "=", values.get("res_paciente")), (
                'create_date', '>=', values.get("start_date")), ('create_date', '<=', values.get("end_date"))])

        notis = []
        contador = 0

        for noti in notificaciones:
            notis.append({
                'id': noti.id,
                'mensaje': noti.mensaje,
                'fecha': noti.create_date.strftime('%d/%m/%Y'),
                'leido': noti.mensaje_leido
            })
            if not noti.mensaje_leido:
                contador = contador+1

        for info in datos:
            label.append(info.create_date.strftime('%d/%m/%Y'))

        return {'data': {'datasets': datasets, 'labels': label, 'legend': ['BPMs', 'SpO2']}, 'notificacion': {'datos': notis, 'contador': contador}}

    @http.route('/api/actNoti', auth='public', type='json', csrf=False, methods=["PUT"])
    def actualizar_notificaciones(self, **kw):
        values = request.httprequest.data and json.loads(
            request.httprequest.data.decode('utf-8')) or {}
        datos = request.env["tesis.prescripcion"].sudo().search(
            [("res_paciente", "=", values.get("res_paciente")), ('mensaje_leido', '!=', True)])
        for dato in datos:
            dato.write({'mensaje_leido': True})
        result = {'mensaje': 'Mensaje actualizado', 'success': True}
        return result
