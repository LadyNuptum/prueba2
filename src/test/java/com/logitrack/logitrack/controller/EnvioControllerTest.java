package com.logitrack.logitrack.controller;

import com.logitrack.logitrack.dto.EnvioDTO;
import com.logitrack.logitrack.model.Envio;
import com.logitrack.logitrack.service.EnvioService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;


@ExtendWith(MockitoExtension.class)
class EnvioControllerTest {

    @Mock
    private EnvioService envioService;

    @InjectMocks
    private EnvioController envioController;

    //TESTS USANDO PATRON given-when-then
    @Test
    void getAllEnvios_deberiaRetornarListaDeEnviosDTO(){
        //Preparar
        Envio envio1 = new Envio("1","Cliente 1", "Bogota",10.5,"Pendiente");
        Envio envio2 = new Envio("2","Cliente 2", "Medellin",20.5,"En_ruta");

        List<Envio> envios = Arrays.asList(envio1,envio2);

        //simular
        when(envioService.findAll()).thenReturn(envios);

        //ejecutar
        List<EnvioDTO> resultado = envioController.getAllEnvios();

        //validar
        assertEquals(2,resultado.size());
        assertEquals("Cliente 1", resultado.get(0).getCliente());

        //Verificar
        verify(envioService, times(1)).findAll();
    }


}