package com.logitrack.logitrack.service;

import com.logitrack.logitrack.model.Envio;
import com.logitrack.logitrack.repository.ConductorRepository;
import com.logitrack.logitrack.repository.EnvioRepository;
import jakarta.persistence.EntityManager;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;


@ExtendWith(MockitoExtension.class)
class EnvioServiceJpaImplTest {

    @Mock
    private EnvioRepository envioRepository;

    @Mock
    private ConductorRepository conductorRepository;

    @Mock
    private EntityManager entityManager;

    @InjectMocks
    private EnvioServiceJpaImpl service;


    @Test
    void save_deberiaCalcularCostoCorrectamenteParaPesoNormalYNacional(){

        //Given
        // Preparar: crear un envio sin costo y sin estado
        Envio envio = new Envio("Cliente test","Bogota",10.0,null,null);

        // Simular: entityManager.persist() no debe hacer nada
        doNothing().when(entityManager).persist(any(Envio.class));

        //When
        //  Ejecuta el guardar envio
        Envio resultado = service.save(envio);

        //Then
        //VALIDAR
        assertEquals(10000.0,resultado.getCosto(), 0.01);
        assertEquals("Pendiente", resultado.getEstado());
    }

/*
    @Test
    void save_deberiaGuardarEnvioCorrectamente(){
        //preparar
        Envio envio = new Envio("Cliente test","Bogota",10.0,"PENDIENTE",null);

        Envio envioGuardado = new Envio("Cliente Test", "Bogota", 10.0,"PENDIENTE",10000.0);

        //SIMULAR
        when(envioRepository.save(any(Envio.class))).thenReturn(envioGuardado);

        //Ejecutar
        Envio resultado = service.save(envio);

        //validar
        assertNotNull(resultado);
        assertEquals(10000.0,resultado.getCosto());

        verify(envioRepository, times(1)).save(any(Envio.class));

    }
    */

    @Test
    void save_deberiaCalcularCostoCorrectamenteParaPesoPesado(){
        //preparar
        Envio envio = new Envio("Cliente test","Bogota",51.0,null,null);

        doNothing().when(entityManager).persist(any(Envio.class));

        Envio resultado = service.save(envio);

        assertNotNull(resultado);
        assertEquals(12000.0,resultado.getCosto(), 0.01);

    }

    @Test
    void save_deberiaCalcularCostoCorrectamenteParaDestinoInternacional(){
        Envio envio = new Envio("Cliente test","Internacional",40.0,null,null);

        //Simulacion
        doNothing().when(entityManager).persist(any(Envio.class));

        Envio resultado = service.save(envio);

        assertEquals(15000.0,resultado.getCosto(), 0.01);
    }

    @Test
    void save_deberiaLanzarExcepcionSiPesoExcedeLimite(){
        Envio envio = new Envio("Cliente test","bogota",600.0,null,null);

        RuntimeException exception = assertThrows(RuntimeException.class, () ->{
            service.save(envio);
        });

        assertEquals("El envio no puede pesar mas de 500kg", exception.getMessage());
        verify(entityManager, never()).persist(any(Envio.class));
    }

}