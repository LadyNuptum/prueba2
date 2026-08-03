package com.logitrack.logitrack.service;

import com.logitrack.logitrack.model.Envio;
import com.logitrack.logitrack.repository.EnvioRepository;
import jakarta.persistence.EntityManager;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class EnvioServiceJpaImpl implements EnvioService{

    private final EnvioRepository envioRepository;

    private final EntityManager entityManager;

    @Autowired
    public EnvioServiceJpaImpl(EnvioRepository envioRepository, EntityManager entityManager){
        this.entityManager = entityManager;
        this.envioRepository = envioRepository;
    }

    @Override
    public List<Envio> findAll() {
        System.out.println("Buscando todos los envios...");
        List<Envio> envios = envioRepository.findAll();
        System.out.println("Encontrados " + envios.size() + " envios.");
        return envios;
    }

    @Override
    public Envio findById(String id) {
        System.out.println("Buscando envio con Id: " +id);
        Optional<Envio> optionalEnvio = envioRepository.findById(id);

        if(optionalEnvio.isPresent()){
            Envio envio = optionalEnvio.get();
            System.out.println("Envio encontrado " + id);
            return envio;
        }else{
            System.out.println("Envio no encontrado con el id: " + id);
            throw new RuntimeException("Envio no encontrado con el id: " + id);
        }
    }

    /* Implementacion sin logica de negocio
    @Override
    public Envio save(Envio envio) {
        System.out.println("Intentando guardar un envio nuevo...");
        System.out.println("Cliente: " + envio.getCliente());
        System.out.println("Destino: " + envio.getDestino());
        System.out.println("Peso: " + envio.getPesoKg());
        System.out.println("Estado: "+ envio.getPesoKg());

        //entityManager.persist(envio);

        System.out.println("Envio guardado correctamente");

        return envioRepository.save(envio);
    }*/

    //Implementacion con logica de negocio
    @Override
    public Envio save(Envio envio) {

        double costo = calcularCostoEnvio(envio.getPesoKg(),
                envio.getDestino());
        envio.setCosto(costo);

        if(envio.getEstado() == null){
            envio.setEstado("Pendiente");
        }

        if(envio.getPesoKg() > 500){
            throw new RuntimeException("El envio no puede pesar mas de 500kg");
        }

        entityManager.persist(envio);
        return envio;
        //return envioRepository.save(envio);

    }


    private double calcularCostoEnvio(Double pesoKg, String destino){

        double costobase = 10000 ;

        if(pesoKg > 50){
            costobase *= 1.2;
        }
        if (destino.equalsIgnoreCase("Internacional")){
            costobase = costobase * 1.5;
        }
        return costobase;
    }

    @Override
    public Envio update(String id, Envio envioActualizado) {
        System.out.println("Intentando actualizar el envio con id: " + id);
        Optional<Envio> optionalEnvio = envioRepository.findById(id);
        if(optionalEnvio.isPresent()){
            envioActualizado.setId(id);
            Envio envioActualizadoGuardado = entityManager.merge(envioActualizado);
            System.out.println("Envio actualizado correctamente.");
            return envioActualizadoGuardado;
        }else{
            System.out.println("Envio no encontrado para poder actualizar");
            throw new RuntimeException("Envio no encontrado para poder actualizar con ID: " + id);
        }
    }

    @Override
    public void deleteById(String id) {
        System.out.println("Intentando eliminar envio con ID: " + id);
        Optional<Envio> optionalEnvio = envioRepository.findById(id);
        if (optionalEnvio.isPresent()){
            envioRepository.deleteById(id);
            System.out.println("Envio Eliminado exitosamente");
        }else{
            System.out.println("Envio no encontrado para eliminar");
            throw new RuntimeException("Envio no encontrado para eliminar con id: "+ id);
        }
    }

    @Override
    public List<Envio> findByEstado(String estado) {
        System.out.println("Buscando los envios bajo el estado: " + estado);
        List<Envio> envios = envioRepository.findByEstado(estado);
        System.out.println("Encontro " + envios.size() + " envios con estado " + estado);
        return envios;
    }
}
